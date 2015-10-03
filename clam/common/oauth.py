#You need to explicitly register your service with your OAuth provider and set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET accordingly

#Copy the remaining the OAUTH_* variables from those here if your provider is listed (replace the name, e.g. GOOGLE_, with OAUTH_) in your settings file:
#   import clam.common.oauth
#   OAUTH_AUTH_URL = clam.common.oauth.GOOGLE_AUTH_URL
#   etc...

from __future__ import print_function, unicode_literals, division, absolute_import

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



def encrypt(encryptionsecret, oauth_access_token, ip):
    BLOCK_SIZE = 16
    c = AES.new(encryptionsecret, AES.MODE_ECB)
    clear = oauth_access_token + ':' + ip
    try:
        clear = str(clear + ((BLOCK_SIZE - len(clear) % BLOCK_SIZE) * " "))
        encoded = base64.urlsafe_b64encode(c.encrypt(clear))
    except:
        #prevent leaks in debug mode
        encryptionsecret = "SECRET"
        oauth_access_token = "SECRET"
        raise OAuthError("Error in access token encryption")
    return encoded

def decrypt(encryptionsecret, oauth_access_token):
    c = AES.new(encryptionsecret, AES.MODE_ECB)
    clear = c.decrypt(base64.urlsafe_b64decode(str(oauth_access_token)))
    try:
        oauth_access_token, ip = clear.strip().split(':')
    except:
        #prevent leaks in debug mode
        encryptionsecret = "SECRET"
        oauth_access_token = "SECRET"
        raise OAuthError("Error in access token decryption")
    return oauth_access_token, ip

