
"""
flask.ext.httpauth (extended for CLAM)
==================

This module provides Basic and Digest HTTP authentication for Flask routes. Adapted and extended for CLAM by Maarten van Gompel.

:copyright: (C) 2014 by Miguel Grinberg.
:license:   BSD, see LICENSE for more details.
"""


import sys
import os
from functools import wraps
from hashlib import md5
from random import Random, SystemRandom
from glob import glob
import time
import flask

import clam.common.oauth
from clam.common.digestauth import pwhash

try:
    from requests_oauthlib import OAuth2Session
except ImportError:
    print( "WARNING: No OAUTH2 support available in your version of Python! Install python-requests-oauthlib if you plan on using OAUTH2 for authentication!", file=sys.stderr)


class NoAuth(object):
    def require_login(self, f, optional=False):
        return f

class HTTPAuth(object):
    def __init__(self, **kwargs):
        def default_get_password(username, **kwargs):
            raise Exception("No get_password function defined")

        def default_auth_error():
            return "Unauthorized Access"

        self.settings = kwargs
        if 'get_password' in kwargs:
            self.set_password_function(kwargs['get_password'])
        else:
            self.set_password_function(default_get_password)
        if 'debug' in kwargs:
            self.printdebug = kwargs['debug']
        else:
            self.printdebug = lambda x: None
        self.error_handler(default_auth_error)

    def set_password_function(self, f):
        """Returns a function that is used to get the password (which is stored as the HA1 of HTTP Digest)"""
        self.get_password = f
        return f

    def error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            flask.request.data #clear receive buffer of pending data
            res = f(*args, **kwargs)
            if isinstance(res, str): #pylint: disable=undefined-variable
                res = flask.make_response(res)
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys() and hasattr(self,'authenticate_header'):
                res.headers['WWW-Authenticate'] = self.authenticate_header()
            return res
        self.auth_error_callback = decorated
        return decorated

    def require_login(self, f, optional=False):
        @wraps(f)
        def decorated(*args, **kwargs):
            self.printdebug("Handling HTTP " + self.scheme + " Authentication")
            auth = flask.request.authorization


            # We need to ignore authentication headers for OPTIONS to avoid
            # unwanted interactions with CORS.
            # Chrome and Firefox issue a preflight OPTIONS request to check
            # Access-Control-* headers, and will fail if it returns 401.
            if flask.request.method != 'OPTIONS':
                if not auth:
                    msg = "No authentication header supplied"
                    self.printdebug(msg)
                    if optional and 'project' not in flask.request.values: #optional login only valid if the project entry shortcut is not used
                        self.printdebug("Login was optional, falling back to anonymous login")
                        kwargs['credentials'] = {'user':'anonymous', '401response': self.auth_error_callback() }
                        return f(*args,**kwargs)
                    else:
                        return self.auth_error_callback()
                if not flask.request.headers['Authorization'].lower().startswith(self.scheme.lower()):
                    msg = "Invalid authentication scheme, expected " + self.scheme
                    self.printdebug(msg)
                    return self.auth_error_callback()
                username = self.username(**self.settings)
                self.printdebug("Obtained username: " + username)
                try:
                    password = self.get_password(username, **self.settings)
                    if not password:
                        self.printdebug("Unable to obtain password for user " + username)
                        return self.auth_error_callback()
                except KeyError:
                    self.printdebug("No such user")
                    return self.auth_error_callback()
                if not self.authenticate(auth, password):
                    return self.auth_error_callback()
                #add username as parameter to the wrapped function
                kwargs['credentials'] = username
            else:
                #add username as parameter to the wrapped function
                self.printdebug("Handling preflight OPTIONS request (no authentication)")
                kwargs['credentials'] = 'anonymous'
            return f(*args,**kwargs)
        return decorated

    def username(self, **kwargs):
        return flask.request.authorization.username


class HTTPBasicAuth(HTTPAuth):

    def __init__(self, **kwargs):
        super(HTTPBasicAuth, self).__init__(**kwargs)
        if 'realm' in kwargs:
            self.realm = kwargs['realm']
        else:
            self.realm = "Default realm"
        self.printdebug("Initialising Basic Authentication with realm " + self.realm)
        self.scheme = "Basic"

    def authenticate_header(self):
        return 'Basic realm="{0}"'.format(self.realm)

    def authenticate(self, auth, stored_password):
        remote_addr = flask.request.remote_addr
        if auth.username is None or self.realm is None or auth.password is None:
            self.printdebug("Basic Authentication challenge *FAILED* for " + auth.username + " due to missing credentials")
            return False
        elif pwhash(auth.username, self.realm, auth.password) == stored_password:
            self.printdebug("Basic Authentication challenge passed by " + remote_addr + " for " + auth.username)
            return True
        else:
            self.printdebug("Basic Authentication challenge *FAILED* by " + remote_addr + " for " + auth.username)
            return False


class HTTPDigestAuth(HTTPAuth):

    def __init__(self, noncedir, **kwargs):
        super(HTTPDigestAuth, self).__init__(**kwargs)
        if 'realm' in kwargs:
            self.realm = kwargs['realm']
        else:
            self.realm = "Default realm"
        self.scheme = "Digest"


        if 'nonceexpiration' in kwargs:
            self.nonceexpiration = int(kwargs['nonceexpiration'])
        else:
            self.nonceexpiration = 900

        self.noncememory = NonceMemory(noncedir, self.nonceexpiration)

        self.printdebug("Initialising Digest Authentication with realm " + self.realm)

        def default_generate_nonce():
            return self.noncememory.getnew(self.nonceexpiration)

        def default_verify_nonce(nonce):
            return self.noncememory.validate(nonce)

        def default_generate_opaque(nonce):
            opaque, ip, expiretime = self.noncememory.get(nonce) #pylint: disable=unused-variable
            return opaque

        def default_verify_opaque(nonce, checkopaque):
            opaque, ip, expiretime = self.noncememory.get(nonce) #pylint: disable=unused-variable
            return opaque == checkopaque

        self.generate_nonce(default_generate_nonce)
        self.generate_opaque(default_generate_opaque)
        self.verify_nonce(default_verify_nonce)
        self.verify_opaque(default_verify_opaque)

    def generate_nonce(self, f):
        self.generate_nonce_callback = f
        return f

    def verify_nonce(self, f):
        self.verify_nonce_callback = f
        return f

    def generate_opaque(self, f):
        self.generate_opaque_callback = f
        return f

    def verify_opaque(self, f):
        self.verify_opaque_callback = f
        return f

    def get_nonce(self):
        return self.generate_nonce_callback()

    def get_opaque(self, nonce):
        return self.generate_opaque_callback(nonce)


    def authenticate_header(self):
        nonce = self.get_nonce()
        opaque = self.get_opaque(nonce)
        return 'Digest realm="{0}",nonce="{1}",opaque="{2}"'.format(self.realm, nonce, opaque)

    def authenticate(self, auth, password): #pylint: disable=too-many-return-statements
        remote_addr = flask.request.remote_addr
        if not auth.username:
            self.printdebug("Username missing in authorization header from " + remote_addr)
            return False
        elif not auth.realm:
            self.printdebug("Realm missing in authorization header from " + remote_addr + " for " + auth.username)
            return False
        elif not auth.uri:
            self.printdebug("URI missing in authorization header from " + remote_addr + " for " + auth.username)
            return False
        elif not auth.nonce:
            self.printdebug("Nonce missing in authorization header from " + remote_addr + " for " + auth.username)
            return False
        elif not  auth.response:
            self.printdebug("Response missing in authorization header from " + remote_addr + " for " + auth.username)
            return False
        elif not password:
            self.printdebug("Password missing from " + remote_addr + " for " + auth.username)
            return False
        elif not self.verify_nonce_callback(auth.nonce):
            self.printdebug("Nonce mismatch from " + remote_addr + " for " + auth.username)
            return False
        elif not self.verify_opaque_callback(auth.nonce, auth.opaque):
            self.printdebug("Opaque mismatch from " + remote_addr + " for " + auth.username)
            return False
        #password is stored has HA1 already
        #a1 = auth.username + ":" + auth.realm + ":" + password
        #ha1 = md5(a1.encode('utf-8')).hexdigest()
        ha1 = password
        a2 = flask.request.method + ":" + auth.uri
        ha2 = md5(a2.encode('utf-8')).hexdigest()
        a3 = ha1 + ":" + auth.nonce + ":" + ha2
        response = md5(a3.encode('utf-8')).hexdigest()
        if response == auth.response:
            self.printdebug("Digest Authentication challenge passed by " + remote_addr + " for " + auth.username)
            return True
        else:
            self.printdebug("Digest Authentication challenge *FAILED* by " + remote_addr + " for " + auth.username)
            return False


class ForwardedAuth(HTTPAuth):
    """Authentication mechanism that simply obtains the user name from a header set by an earlier server-side authentication mechanism"""

    def __init__(self,headers, **kwargs):
        super(ForwardedAuth, self).__init__(**kwargs)
        if isinstance(headers,str):
            self.headers = [headers]
        else:
            self.headers = headers
        self.printdebug("Forwarded authentication listens to headers: " + ",".join(self.headers))

    def authenticate_header(self):
        return None

    def require_login(self, f, optional=False):
        @wraps(f)
        def decorated(*args, **kwargs):
            self.printdebug("Processing forwarded auth")
            # We need to ignore authentication headers for OPTIONS to avoid
            # unwanted interactions with CORS.
            # Chrome and Firefox issue a preflight OPTIONS request to check
            # Access-Control-* headers, and will fail if it returns 401.
            if flask.request.method != 'OPTIONS':
                try:
                    username = self.username(**self.settings)
                except KeyError:
                    self.printdebug("Header not found")
                    return self.auth_error_callback()
                #add username as parameter to the wrapped function
                kwargs['credentials'] = username
            else:
                kwargs['credentials'] = 'anonymous'
            return f(*args, **kwargs)
        return decorated

    def username(self, **kwargs):
        self.printdebug("Checking headers")
        for h in self.headers:
            self.printdebug("Looking for preauth header " + h)
            if h in flask.request.headers:
                self.printdebug("Header found")
                return flask.request.headers[h]
        raise KeyError

class MultiAuth(object):
    def __init__(self, main_auth, *args,**kwargs):
        self.main_auth = main_auth
        self.additional_auth = args
        if 'debug' in kwargs:
            self.printdebug = kwargs['debug']
        else:
            self.printdebug = lambda x: print(x,file=sys.stderr)
        self.printdebug("Initialized multiple authenticators: " + repr(self.main_auth) + "," + repr(self.additional_auth))

    def require_login(self, f, optional=False):
        @wraps(f)
        def decorated(*args, **kwargs):
            remote_addr = flask.request.remote_addr
            self.printdebug("Handling Multiple Authenticators for " + remote_addr)
            selected_auth = None
            scheme = None
            if 'Authorization' in flask.request.headers:
                try:
                    scheme, _creds = flask.request.headers['Authorization'].split( None, 1)
                    self.printdebug("Requested scheme by " + remote_addr + " = " + scheme)
                except ValueError:
                    # malformed Authorization header
                    self.printdebug("Malformed authorization header from " + remote_addr)
                    pass
                for auth in self.additional_auth:
                    if auth.scheme == scheme:
                        selected_auth = auth
                        break
            elif isinstance(self.main_auth, OAuth2) and self.main_auth.get_oauth_access_token_from_request():
                scheme = "Bearer"
                selected_auth = self.main_auth
            else:
                self.printdebug("No authorization header passed by " + remote_addr)

                if optional:
                    self.printdebug("Login was optional, falling back to anonymous login")
                    #prepare a DEFERRED 401 response, won't be sent immediately
                    #special case to return multiple WWW-Authenticate headers

                    res = flask.make_response("Authorization required")
                    res.status_code = 401
                    value = self.main_auth.authenticate_header()
                    if value:
                        res.headers.add('WWW-Authenticate',  value)
                    for auth in self.additional_auth:
                        value = auth.authenticate_header()
                        if value:
                            res.headers.add('WWW-Authenticate',  value)
                    kwargs['credentials'] = {'user': 'anonymous','401response': res}

                    #return result WITHOUT authentication
                    return f(*args,**kwargs)


                if 'requestauth' in flask.request.values or 'requestauth' in flask.request.cookies:
                    #authentication of a different type explicitly requested

                    if 'requestauth' in flask.request.values:
                        scheme = flask.request.values['requestauth']
                        self.printdebug("Requested scheme (in params) by " + remote_addr + " = " + scheme)
                    else:
                        scheme = flask.request.cookies['requestauth']
                        self.printdebug("Requested scheme (in cookie) by " + remote_addr + " = " + scheme)
                    if scheme != self.main_auth.scheme:
                        for auth in self.additional_auth:
                            if auth.scheme == scheme:
                                self.printdebug("Using to requested authentication scheme")
                                res = auth.require_login(f, optional)(*args, **kwargs)
                                self.printdebug("Setting cookie")
                                res.set_cookie('requestauth', scheme)
                                return res

                #main authentication method determines whether this will be a 401 or immediately a 302 (oauth)
                res = self.main_auth.require_login(f, optional)(*args, **kwargs)
                for auth in self.additional_auth:
                    value = auth.authenticate_header()
                    if value:
                        res.headers.add('WWW-Authenticate',  value)
                return res

            if selected_auth is None:
                selected_auth = self.main_auth
            return selected_auth.require_login(f, optional)(*args, **kwargs)
        return decorated

class OAuth2(HTTPAuth):
    def __init__(self, client_id, auth_url, redirect_url, auth_function, username_function, debug=None, scope=None, userinfo_url=None): #pylint: disable=super-init-not-called
        def default_auth_error():
            res = flask.make_response("Unauthorized Access (OAuth2). Your access token may be invalid or is expired, if the latter is the case, simply refresh the page to be redirected login again.")
            res.set_cookie('oauth_access_token', "",expires=0) #remove cookie
            res.status_code = 403
            return res



        self.client_id = client_id
        self.auth_url = auth_url #Remote URL
        self.auth_function = auth_function
        self.username_function = username_function
        self.redirect_url = redirect_url #the /login URL of the webservice
        self.userinfo_url = userinfo_url
        self.scope = scope
        if debug:
            self.printdebug = debug
        else:
            self.printdebug = lambda x: print(x,file=sys.stderr)
        self.scheme = "Bearer"
        self.error_handler(default_auth_error)

    def authenticate_header(self):
        #provide forward to login (the caller can decide whether to actually use this)
        kwargslogin = {'redirect_uri': self.redirect_url}
        if self.scope:
            kwargslogin['scope'] = self.scope
        oauthsession = OAuth2Session(self.client_id, **kwargslogin)
        if self.userinfo_url: oauthsession.USERINFO_URL = self.userinfo_url
        auth_url, _state = self.auth_function(oauthsession, self.auth_url)
        return 'Bearer auth_server="{0}"'.format(auth_url) #following https://stackoverflow.com/questions/50921816/standard-http-header-to-indicate-location-of-openid-connect-server , realm is OPTIONAL so I skip it here

    def get_oauth_access_token_from_request(self):
        oauth_access_token = None
        try:
            authheader = flask.request.headers['Authorization']
        except KeyError:
            authheader = None
        #Obtain access token
        if authheader and authheader[:6].lower() == "bearer":
            oauth_access_token = authheader[7:]
            self.printdebug("Oauth access token obtained from HTTP request Authentication header")
        elif authheader and authheader[:5].lower() == "token":
            oauth_access_token = authheader[6:]
            self.printdebug("Oauth access token obtained from HTTP request Authentication header")
        else:
            #Is the token submitted via a cookie?
            oauth_access_token = flask.request.cookies.get("oauth_access_token")
            if not oauth_access_token:
                self.printdebug("Oauth access token not found in cookie")
                #Is the token submitted in the GET/POST data? (as oauth_access_token)
                #This is a last resort we don't really want to use
                try:
                    oauth_access_token = flask.request.values['oauth_access_token']
                    self.printdebug("Oauth access token obtained from HTTP request GET/POST data")
                except KeyError:
                    self.printdebug("No oauth access token found. Header debug: " + repr(flask.request.headers) )
            else:
                self.printdebug("Oauth access token obtained from cookie")

        return oauth_access_token

    def require_login(self, f, optional=False):
        @wraps(f)
        def decorated(*args, **kwargs):
            # We need to ignore authentication headers for OPTIONS to avoid
            # unwanted interactions with CORS.
            # Chrome and Firefox issue a preflight OPTIONS request to check
            # Access-Control-* headers, and will fail if it returns 401.
            if flask.request.method != 'OPTIONS':
                oauth_access_token = self.get_oauth_access_token_from_request()

                if not oauth_access_token:
                    #No access token yet, start login process
                    if optional:
                        #unless logins are optional...
                        self.printdebug("Login was optional, falling back to anonymous login")

                        #forward to login (the caller can decide whether to use this)
                        kwargslogin = {'redirect_uri': self.redirect_url}
                        if self.scope:
                            kwargslogin['scope'] = self.scope
                        oauthsession = OAuth2Session(self.client_id, **kwargslogin)
                        if self.userinfo_url: oauthsession.USERINFO_URL = self.userinfo_url
                        auth_url, state = self.auth_function(oauthsession, self.auth_url) #pylint: disable=unused-variable
                        kwargs['credentials'] = {'user': 'anonymous','401response': flask.redirect(auth_url)}

                        return f(*args,**kwargs)

                    self.printdebug("No access token available yet, starting login process")

                    kwargs = {'redirect_uri': self.redirect_url}
                    if self.scope:
                        kwargs['scope'] = self.scope
                    self.printdebug("OAuth2 details, client=" + self.client_id + ": " + repr(kwargs))
                    oauthsession = OAuth2Session(self.client_id, **kwargs)
                    if self.userinfo_url: oauthsession.USERINFO_URL = self.userinfo_url
                    auth_url, state = self.auth_function(oauthsession, self.auth_url) #pylint: disable=unused-variable

                    #Redirect to Authentication Provider
                    self.printdebug("Redirecting to authentication provider: " + self.auth_url)

                    return flask.redirect(auth_url)
                else:
                    oauthsession = OAuth2Session(self.client_id, token={'access_token': oauth_access_token, 'token_type': 'bearer'})
                    if self.userinfo_url: oauthsession.USERINFO_URL = self.userinfo_url
                    try:
                        username = self.username_function(oauthsession)
                    except clam.common.oauth.OAuthError as e:
                        self.printdebug("Could not obtain username from OAuth session, got OAuthError error " + str(e))
                        return self.auth_error_callback()
                    if username:
                        #add (username, oauth_access_token) tuple as parameter to the wrapped function
                        kwargs['credentials'] =  (username, oauth_access_token)
                        return f(*args, **kwargs)
                    else:
                        self.printdebug("Could not obtain username from OAuth session")
                        return self.auth_error_callback()
            else:
                #what do we do if request method is OPTIONS?
                kwargs['credentials'] = 'anonymous'
            return f(*args,**kwargs)
        return decorated

class NonceMemory:
    """File-based nonce-memory (so it can work with multiple workers). Includes expiration per nonce and and IP-check"""

    def __init__(self, path, expiration,debug=False):
        self.path = path
        self.expiration = expiration
        self.debug = debug

        self.random = SystemRandom()
        try:
            self.random.random()
        except NotImplementedError:
            self.random = Random() #pylint: disable=redefined-variable-type

    def getnew(self, expiration=None, opaque=None):
        if expiration is None: expiration = self.expiration
        self.cleanup() #first cleanup current nonces before making a new one, this has some I/O overhead but amount of nonces should be limited
        nonce = md5(str(self.random.random()).encode('utf-8')).hexdigest()
        if self.debug: print("Generated new nonce " + nonce,file=sys.stderr)
        if opaque is None:
            #Generate a random opaque if none was given
            opaque = md5(str(self.random.random()).encode('utf-8')).hexdigest()
        with open(self.path + '/' + nonce + '.nonce','w') as f:
            f.write(opaque + "\n")
            f.write(flask.request.remote_addr + "\n")
            f.write(str(time.time() + expiration) + "\n")
        return nonce

    def validate(self, nonce):
        """Does the nonce exist and is it valid for the request?"""
        if self.debug: print("Checking nonce " + str(nonce),file=sys.stderr)
        try:
            opaque, ip, expiretime = self.get(nonce) #pylint: disable=unused-variable
            if expiretime < time.time():
                if self.debug: print("Nonce expired",file=sys.stderr)
                self.remove(nonce)
                return False
            elif ip != flask.request.remote_addr:
                if self.debug: print("Nonce IP mismatch",file=sys.stderr)
                self.remove(nonce)
                return False
            else:
                return True
        except KeyError:
            if self.debug: print("Nonce " + nonce + " does not exist",file=sys.stderr)
            return False

    def remove(self, nonce):
        noncefile = self.path + '/' + nonce + '.nonce'
        if os.path.exists(noncefile):
            os.unlink(noncefile)

    def get(self, nonce):
        if not nonce: raise KeyError("No nonce supplied")
        noncefile = self.path + '/' + nonce + '.nonce'
        if os.path.exists(noncefile):
            return self.readnoncefile(noncefile) #returns (opaque,ip,expiretime) tuple
        else:
            raise KeyError("No such nonce: " + nonce)

    def readnoncefile(self, noncefile):
        with open(noncefile,'r') as f:
            opaque = f.readline().strip()
            ip = f.readline().strip()
            expiretime = float(f.readline().strip())
        return (opaque, ip, expiretime)


    def cleanup(self):
        """Delete expired nonces"""
        t = time.time()
        for noncefile in glob(self.path + '/*.nonce'):
            if os.path.getmtime(noncefile) + self.expiration > t:
                os.unlink(noncefile)

