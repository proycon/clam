
"""
flask.ext.httpauth (extended for CLAM)
==================

This module provides Basic and Digest HTTP authentication for Flask routes. Adapted and extended for CLAM by Maarten van Gompel.

:copyright: (C) 2014 by Miguel Grinberg.
:license:   BSD, see LICENSE for more details.
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
from functools import wraps
from hashlib import md5
from random import Random, SystemRandom
from glob import glob
import time
import flask

import clam.common.oauth

try:
    from requests_oauthlib import OAuth2Session
except ImportError:
    print( "WARNING: No OAUTH2 support available in your version of Python! Install python-requests-oauthlib if you plan on using OAUTH2 for authentication!", file=sys.stderr)


class NoAuth(object):
    def require_login(self, f):
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
            res = f(*args, **kwargs)
            if (sys.version >= '3' and isinstance(res, str)) or (sys.version < '3' and isinstance(res,unicode)): #pylint: disable=undefined-variable
                res = flask.make_response(res)
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys() and hasattr(self,'authenticate_header'):
                res.headers['WWW-Authenticate'] = self.authenticate_header()
            return res
        self.auth_error_callback = decorated
        return decorated

    def require_login(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = flask.request.authorization
            # We need to ignore authentication headers for OPTIONS to avoid
            # unwanted interactions with CORS.
            # Chrome and Firefox issue a preflight OPTIONS request to check
            # Access-Control-* headers, and will fail if it returns 401.
            if flask.request.method != 'OPTIONS':
                if not auth:
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
        self.hash_password(None)
        self.verify_password(None)

    def hash_password(self, f):
        self.hash_password_callback = f
        return f

    def verify_password(self, f):
        self.verify_password_callback = f
        return f


    def authenticate(self, auth, stored_password):
        client_password = auth.password
        if self.verify_password_callback:
            return self.verify_password_callback(auth.username, client_password)
        if self.hash_password_callback:
            try:
                client_password = self.hash_password_callback(client_password)
            except TypeError:
                client_password = self.hash_password_callback(auth.username, client_password)
        return client_password == stored_password


class HTTPDigestAuth(HTTPAuth):
    def __init__(self, noncedir, **kwargs):
        super(HTTPDigestAuth, self).__init__(**kwargs)
        if 'realm' in kwargs:
            self.realm = kwargs['realm']
        else:
            self.realm = "Default realm"


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
        if not auth.username:
            self.printdebug("Username missing in authorization header")
            return False
        elif not auth.realm:
            self.printdebug("Realm missing in authorization header")
            return False
        elif not auth.uri:
            self.printdebug("URI missing in authorization header")
            return False
        elif not auth.nonce:
            self.printdebug("Nonce missing in authorization header")
            return False
        elif not  auth.response:
            self.printdebug("Response missing in authorization header")
            return False
        elif not password:
            self.printdebug("Password missing")
            return False
        elif not self.verify_nonce_callback(auth.nonce):
            self.printdebug("Nonce mismatch")
            return False
        elif not self.verify_opaque_callback(auth.nonce, auth.opaque):
            self.printdebug("Opaque mismatch")
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
            self.printdebug("Authentication challenge passed")
            return True
        else:
            self.printdebug("Authentication challenge failed")
            return False


class ForwardedAuth(HTTPAuth):
    """Authentication mechanism that simply obtains the user name from a header set by an earlier server-side authentication mechanism"""

    def __init__(self,headers, **kwargs):
        super(ForwardedAuth, self).__init__(**kwargs)
        if isinstance(headers,str):
            self.headers = [headers]
        else:
            self.headers = headers

    def authenticate_header(self):
        return flask.make_response('Pre-authentication mechanism did not pass expected header',403)

    def require_login(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = flask.request.authorization
            # We need to ignore authentication headers for OPTIONS to avoid
            # unwanted interactions with CORS.
            # Chrome and Firefox issue a preflight OPTIONS request to check
            # Access-Control-* headers, and will fail if it returns 401.
            if flask.request.method != 'OPTIONS':
                if not auth:
                    return self.auth_error_callback()
                try:
                    username = self.username(**self.settings)
                except KeyError:
                    return self.auth_error_callback()
                #add username as parameter to the wrapped function
                kwargs['credentials'] = username
            else:
                kwargs['credentials'] = 'anonymous'
            return f(*args, **kwargs)
        return decorated

    def username(self, **kwargs):
        for h in self.headers:
            if h in flask.request.headers:
                return flask.request.headers[h]
        raise KeyError

class OAuth2(HTTPAuth):
    def __init__(self, client_id, encryptionsecret, auth_url, redirect_url, auth_function, username_function, printdebug=None, scope=None): #pylint: disable=super-init-not-called
        def default_auth_error():
            return "Unauthorized Access (OAuth2)"


        self.client_id = client_id
        self.encryptionsecret = encryptionsecret
        self.auth_url = auth_url #Remote URL
        self.auth_function = auth_function
        self.username_function = username_function
        self.redirect_url = redirect_url #the /login URL of the webservice
        self.scope = scope
        if printdebug:
            self.printdebug = printdebug
        else:
            self.printdebug = lambda x: print(x,file=sys.stderr)
        self.error_handler(default_auth_error)

    def require_login(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                authheader = flask.request.headers['Authorization']
            except KeyError:
                authheader = None
            # We need to ignore authentication headers for OPTIONS to avoid
            # unwanted interactions with CORS.
            # Chrome and Firefox issue a preflight OPTIONS request to check
            # Access-Control-* headers, and will fail if it returns 401.
            if flask.request.method != 'OPTIONS':
                oauth_access_token = None
                #Obtain access token
                if authheader and authheader[:6].lower() == "bearer":
                    oauth_access_token = authheader[7:]
                    self.printdebug("Oauth access token obtained from HTTP request Authentication header")
                elif authheader and authheader[:5].lower() == "token":
                    oauth_access_token = authheader[6:]
                    self.printdebug("Oauth access token obtained from HTTP request Authentication header")
                else:
                    #Is the token submitted in the GET/POST data? (as oauth_access_token)
                    try:
                        oauth_access_token = flask.request.values['oauth_access_token']
                        self.printdebug("Oauth access token obtained from HTTP request GET/POST data")
                    except KeyError:
                        self.printdebug("No oauth access token found. Header debug: " + repr(flask.request.headers) )

                if not oauth_access_token:
                    #No access token yet, start login process
                    self.printdebug("No access token available yet, starting login process")

                    #redirect_url = getrooturl() + '/login'

                    kwargs = {'redirect_uri': self.redirect_url}
                    if self.scope:
                        kwargs['scope'] = self.scope
                    oauthsession = OAuth2Session(self.client_id, **kwargs)
                    auth_url, state = self.auth_function(oauthsession, self.auth_url) #pylint: disable=unused-variable

                    #Redirect to Authentication Provider
                    self.printdebug("Redirecting to authentication provider: " + self.auth_url)

                    return flask.redirect(auth_url)
                else:
                    #Decrypt access token
                    try:
                        oauth_access_token, ip = clam.common.oauth.decrypt(self.encryptionsecret, oauth_access_token)
                    except clam.common.oauth.OAuthError:
                        self.printdebug("Error decrypting access token")
                        return self.auth_error_callback()
                        #return flask.make_response("Error decrypting access token",403)

                    if ip != flask.request.headers.get('REMOTE_ADDR', ''):
                        self.printdebug("Access token not valid for IP, got " + ip + ", expected " + flask.request.headers.get('REMOTE_ADDR',''))
                        #return flask.make_response("Access token not valid for this IP",403)
                        return self.auth_error_callback()

                    oauthsession = OAuth2Session(self.client_id, token={'access_token': oauth_access_token, 'token_type': 'bearer'})
                    username = self.username_function(oauthsession)
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


