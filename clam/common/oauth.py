#You need to explicitly register your service with your OAuth provider and set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET accordingly

#Copy the remaining the OAUTH_* variables from those here if your provider is listed (replace the name, e.g. GOOGLE_, with OAUTH_) in your settings file:
#   import clam.common.oauth
#   OAUTH_AUTH_URL = clam.common.oauth.GOOGLE_AUTH_URL
#   etc...


import sys
import json
import base64
from requests_oauthlib import OAuth2Session

class OAuthError(Exception):
    pass

def DEFAULT_AUTH_FUNCTION(oauthsession, authurl):
    """Default auth function, returns auth_url, state tuple"""
    return oauthsession.authorization_url(authurl)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'
GOOGLE_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]
GOOGLE_AUTH_FUNCTION = lambda oauthsession, authurl: oauthsession.authorization_url(authurl, access_type="offline",approval_prompt="force")

GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USERINFO_URL = 'https://api.github.com/user'

def GITHUB_USERNAME_FUNCTION(oauthsession):
    r = oauthsession.get(GITHUB_USERINFO_URL)
    rj = json.loads(str(r.content,'utf-8'))
    if not 'login' in rj:
        raise OAuthError("Login not found in json reply from github: " + repr(rj))
    return rj['login']

FACEBOOK_AUTH_URL= 'https://www.facebook.com/dialog/oauth'
FACEBOOK_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
FACEBOOK_USERINFO_URL = 'https://graph.facebook.com/me?'


def DEFAULT_USERNAME_FUNCTION(oauthsession):
    """Generic username function, should be suitable for OpenID Connect"""
    if not hasattr(oauthsession, 'USERINFO_URL'):
        raise OAuthError("You did not specify a OAUTH_USERINFO_URL in your service configuration")
    r = oauthsession.get(oauthsession.USERINFO_URL)
    rj = json.loads(str(r.content,'utf-8'))
    for key in ('email','mail','login','user','username','name','userid','eppn','id'):
        if key in rj:
            return rj[key]
    raise OAuthError("No username (checked email and various fallbacks) was found in json reply from userinfo endpoint: " + repr(rj))

