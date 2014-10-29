#You need to explicitly register your service with your OAuth provider and set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET accordingly

#Copy the remaining the OAUTH_* variables from those here if your provider is listed (replace the name, e.g. GOOGLE_, with OAUTH_) in your settings file:
#   import clam.common.oauth
#   OAUTH_AUTH_URL = clam.common.oauth.GOOGLE_AUTH_URL
#   etc...

import json
from requests_oauthlib import OAuth2Session
from Crypto.Cipher import AES
import base64

class OAuthError(Exception):
    pass

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
GOOGLE_SCOPE = [
     "https://www.googleapis.com/auth/userinfo.email",
     "https://www.googleapis.com/auth/userinfo.profile"
]
GOOGLE_AUTH_FUNCTION = lambda oauthsession, authurl: oauthsession.authorization_url(authurl, access_type="offline",approval_prompt="force")

def GOOGLE_USERNAME_FUNCTION(oauthsession):
    r = oauthsession.get('https://www.googleapis.com/oauth2/v1/userinfo')
    return r.content #TODO: parse and get username!!!!!

GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'

def GITHUB_USERNAME_FUNCTION(oauthsession):
    r = oauthsession.get('https://api.github.com/user')
    rj = json.loads(r.content)
    if not 'login' in rj:
        raise OAuthError("Login not found in json reply from github: " + repr(rj))
    return rj['login']

FACEBOOK_AUTH_URL= 'https://www.facebook.com/dialog/oauth'
FACEBOOK_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'

def FACEBOOK_USERNAME_FUNCTION(oauthsession):
    r = oauthsession.get('https://graph.facebook.com/me?')
    return r.content #TODO: parse and get username!!!!!




class auth(object):
    def __init__(self, client_id, oauth_access_token, username_function):
        oauthsession = OAuth2Session(client_id, token={'access_token': oauth_access_token, 'token_type': 'bearer'})
        self.username = username_function(oauthsession)
        self.oauth_access_token = oauth_access_token


    def __call__(self, f):
        def wrapper(*arguments, **keywords):
            if not (self.username is None):
                arguments += ( (self.username, self.oauth_access_token) ,)
                return f(*arguments, **keywords)
            else:
                raise OAuthError("No valid username returned by OAUTH_USERNAME_FUNCTION")
        return wrapper

def encrypt(encryptionsecret, oauth_access_token, ip):
    BLOCK_SIZE = 16
    c = AES.new(encryptionsecret, AES.MODE_ECB)
    clear = oauth_access_token + ':' + ip
    clear = str(clear + ((BLOCK_SIZE - len(clear) % BLOCK_SIZE) * " "))
    return base64.urlsafe_b64encode(c.encrypt(clear))

def decrypt(encryptionsecret, oauth_access_token):
    c = AES.new(encryptionsecret, AES.MODE_ECB)
    clear = c.decrypt(base64.urlsafe_b64decode(str(oauth_access_token)))
    oauth_access_token, ip = clear.split(':')
    return oauth_access_token.strip(), ip

