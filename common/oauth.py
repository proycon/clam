#You need to explicitly register your service with your OAuth provider and set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET accordingly

#Copy the remaining the OAUTH_* variables from those here if your provider is listed (replace the name, e.g. GOOGLE_, with OAUTH_) in your settings file:
#   import clam.common.oauth
#   OAUTH_AUTH_URL = clam.common.oauth.GOOGLE_AUTH_URL
#   etc...

import json
import web

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
    def __init__(self, oauthsession, username_function):
        try:
            self.username = username_function(oauthsession)
        except:
            self.username = None


    def __call__(self,  oauth_access_token, f):
        def wrapper(*arguments, **keywords):
            if self.username is None:
                arguments += ( (self.username, oauth_access_token) ,)
                return f(*arguments, **keywords)
            else:
                raise OAuthError("No valid username returned by OAUTH_USERNAME_FUNCTION")
        return wrapper
