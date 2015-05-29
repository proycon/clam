
"""
flask.ext.httpauth (extended for CLAM)
==================

This module provides Basic and Digest HTTP authentication for Flask routes. Adapted and extended for CLAM by Maarten van Gompel.

:copyright: (C) 2014 by Miguel Grinberg.
:license:   BSD, see LICENSE for more details.
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
from functools import wraps
from hashlib import md5
from random import Random, SystemRandom
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
            return None

        def default_auth_error():
            return "Unauthorized Access"

        self.settings = kwargs
        if 'get_password' in kwargs:
            self.get_password(kwargs['get_password'])
        else:
            self.get_password(default_get_password)
        self.error_handler(default_auth_error)

    def get_password(self, f):
        self.get_password_callback = f
        return f

    def error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            if type(res) == str:
                res = flask.make_response(res)
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys() and hasattr(self,'authenticate_header'):
                res.headers['WWW-Authenticate'] = self.authenticate_header()
            return res
        self.auth_error_callback = decorated
        return decorated

    def login_required(self, f):
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
                password = self.get_password_callback(username, **self.settings)
                if not self.authenticate(auth, password):
                    return self.auth_error_callback()
                args.append(username)#add username as parameter to the wrapped function
            else:
                args.append('anonymous')
            return f(*args, **kwargs)
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
    def __init__(self, **kwargs):
        super(HTTPDigestAuth, self).__init__(**kwargs)
        if 'realm' in kwargs:
            self.realm = kwargs['realm']
        else:
            self.realm = "Default realm"
        self.random = SystemRandom()
        try:
            self.random.random()
        except NotImplementedError:
            self.random = Random()

    def get_nonce(self):
        return md5(str(self.random.random()).encode('utf-8')).hexdigest()

    def authenticate_header(self):
        flask.session["auth_nonce"] = self.get_nonce()
        flask.session["auth_opaque"] = self.get_nonce()
        return 'Digest realm="{0}",nonce="{1}",opaque="{2}"'.format(self.realm, flask.session["auth_nonce"], flask.session["auth_opaque"])

    def authenticate(self, auth, password):
        if not auth.username or not auth.realm or not auth.uri \
                or not auth.nonce or not auth.response or not password:
            return False
        if auth.nonce != flask.session.get("auth_nonce") or \
                auth.opaque != flask.session.get("auth_opaque"):
            return False
        a1 = auth.username + ":" + auth.realm + ":" + password
        ha1 = md5(a1.encode('utf-8')).hexdigest()
        a2 = flask.request.method + ":" + auth.uri
        ha2 = md5(a2.encode('utf-8')).hexdigest()
        a3 = ha1 + ":" + auth.nonce + ":" + ha2
        response = md5(a3.encode('utf-8')).hexdigest()
        return response == auth.response


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

    def login_required(self, f):
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
                args.append(username) #add username as parameter to the wrapped function
            return f(*args, **kwargs)
        return decorated

    def username(self, **kwargs):
        for h in self.headers:
            if h in flask.request.headers:
                return flask.request.headers[h]
        raise KeyError

class OAuth2(HTTPAuth):
    def __init__(self, client_id, encryptionsecret, auth_url, redirect_url, auth_function, username_function, printdebug=None, scope=None):
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

    def login_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            authheader = flask.request.headers['authorization']
            oauth_access_token = None
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
                except:
                    self.printdebug("No oauth access token found. Header debug: " + repr(flask.request.headers))

            if not oauth_access_token:
                #No access token yet, start login process
                self.printdebug("No access token available yet, starting login process")

                #redirect_url = getrooturl() + '/login'

                kwargs = {'redirect_uri': self.redirect_url}
                if settings.OAUTH_SCOPE:
                    kwargs['scope'] = self.scope
                oauthsession = OAuth2Session(client_id, **kwargs)
                auth_url, state = self.auth_function(oauthsession, self.auth_url)

                #Redirect to Authentication Provider
                self.printdebug("Redirecting to authentication provider: " + self.auth_url)

                return flask.redirect(auth_url)
            else:
                #Decrypt access token
                try:
                    oauth_access_token, ip = clam.common.oauth.decrypt(settings.OAUTH_ENCRYPTIONSECRET, oauth_access_token)
                except clam.common.oauth.OAuthError:
                    return flask.make_response("Error decrypting access token",403)

                if ip != flask.request.headers.get('REMOTE_ADDR', ''):
                    self.printdebug("Access token not valid for IP, got " + ip + ", expected " + flask.request.headers.get('REMOTE_ADDR',''))
                    return flask.make_response("Access token not valid for this IP",403)

                oauthsession = OAuth2Session(client_id, token={'access_token': oauth_access_token, 'token_type': 'bearer'})
                username = self.username_function(oauthsession)
                if username:
                    args.append( (username, oauth_access_token) ) #add (username, oauth_access_token)tuple as parameter to the wrapped function
                    return f(*args, **kwargs)
                else:
                    return flask.make_response("Could not obtain username from OAuth session",403)
        return decorated


