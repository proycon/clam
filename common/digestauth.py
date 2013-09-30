#  By Josh Goldoot
# version 0.01
#  Public domain.

import web
import random, time, re

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5


def pwhash(user, realm, password):
    #computes a password hash for a given user and plaintext password (HA1)
    return md5(user + ':' + realm + ':' + password).hexdigest()



class MalformedAuthenticationHeader(Exception): pass

## Fundamental utilities


class auth(object):
    """A decorator class implementing digest authentication (RFC 2617)"""
    def __init__(self,  getHA1,  realm="Protected",  printdebug = None, urlprefix = None, tolerateIE = True, redirectURL = '/unauth',  unauthHTML = None,  nonceSkip = 0, staticopaque=None, lockTime = 20,  nonceLife = 3600*2,  tries=3,  domain=[]):
        """Creates a decorator specific to a particular web application.
            getHA1: a function taking the arguments (username, realm), and returning digestauth.H(username:realm:password), or
                            throwing KeyError if no such user
            realm: the authentication "realm"
            tolerateIE: don't deny requests from Internet Explorer, even though it is standards uncompliant and kind of insecure
            redirectURL:  when user hits "cancel," they are redirected here
            unauthHTML:  the HTML that is sent to the user and displayed if they hit cancel (default is a redirect page to redirectURL)
            nonceSkip: tolerate skips in the nonce count, only up to this amount (useful if CSS or JavaScript is being loaded unbeknownst to your code)
            lockTime: number of seconds a user is locked out if they send a wrong password (tries) times
            nonceLife: number of seconds a nonce remains valid
            tries: number of tries a user gets to enter a correct password before the account is locked for lockTime seconds
        """
        self.getHA1,  self.realm,  self.tolerateIE,  self.nonceSkip = (getHA1,  realm,  tolerateIE,  nonceSkip)
        self.lockTime,  self.tries,  self.nonceLife,  self.domain = (lockTime,  tries - 1,  nonceLife,  domain)
        self.unauthHTML = unauthHTML or self.g401HTML.replace("$redirecturl",  redirectURL)
        self.printdebug = printdebug
        self.urlprefix = urlprefix
        self.outstandingNonces = NonceMemory()
        self.user_status = {}
        if staticopaque:
            if self.printdebug: self.printdebug("DEBUG set opaque from settings: '" + str(staticopaque) + "'")
            self.opaque = staticopaque
        else:
            if self.printdebug: self.printdebug("DEBUG generated opaque: '" + str(self.opaque)+ "'")
            self.opaque = "%032x" % random.getrandbits(128)

        self.webpy2 = web.__version__.startswith('0.2')
    g401HTML = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <!--<meta http-equiv="REFRESH" content="2; URL=$redirecturl" />-->
  <title>CLAM</title>
</head>
<body>
<p>Authentication required</p>
</body>
</html>
"""
    def __call__(self,  f):
        def wrapper(*arguments,  **keywords):
            requestHeader = web.ctx.environ.get('HTTP_AUTHORIZATION', None)
            if not requestHeader:
                # client has failed to include an authentication header; send a 401 response
                if self.printdebug: self.printdebug("AUTH DEBUG norequestheader")
                return self.send401UnauthorizedResponse()
            if requestHeader[0:7] != "Digest ":
                # client has attempted to use something other than Digest authenication; deny
                if self.printdebug: self.printdebug("AUTH DEBUG badrequest: no digest auth used")
                return self.denyBadRequest()
            reqHeaderDict = parseAuthHeader(requestHeader)
            if not self.directiveProper(reqHeaderDict, web.ctx.fullpath):
                if self.printdebug: self.printdebug("AUTH DEBUG notdirectiveproper")
                # Something is wrong with the authentication header
                if reqHeaderDict.get('opaque',self.opaque) != self.opaque:
                    # Didn't send back the correct "opaque;" probably, our server restarted.  Just send
                    # them another authentication header with the correct opaque field.
                    if self.printdebug: self.printdebug("AUTH DEBUG incorrect opaque: '"+ str(reqHeaderDict.get('opaque',self.opaque)) + "' should be '" + str(self.opaque) + "'")
                    return self.send401UnauthorizedResponse()
                else:
                    # Their header had a more fundamental problem.  Something is fishy.  Deny access.
                    if self.printdebug: self.printdebug("AUTH DEBUG bad request: not conforming to RFC 2617 ")
                    return self.denyBadRequest("Authorization Request Header does not conform to RFC 2617 section 3.2.2")
            # if user sent a "logout" nonce, make them type in the password again
            if len(reqHeaderDict.nonce) != 34:
                if printdebug: printdebug("DEBUG logoutnonce")
                return self.send401UnauthorizedResponse()
            nonceReaction = self.outstandingNonces.nonceState(reqHeaderDict,  self.nonceSkip)
            if nonceReaction == 2:
                # Client sent a nonce we've never heard of before
                if self.printdebug: self.printdebug("AUTH DEBUG unknownnonce")
                return self.send401UnauthorizedResponse() #this seems more logical to me, otherwise we get bad request in case of server restart
                #return self.denyBadRequest() #original
            if nonceReaction == 3:
                # Client sent an old nonce.  Give the client a new one, and ask to authenticate again before continuing.
                if self.printdebug: self.printdebug("AUTH DEBUG oldnonce")
                return self.send401UnauthorizedResponse(stale=True)
            username = reqHeaderDict.username
            if self.printdebug: self.printdebug("AUTH DEBUG user="+username)
            status = self.user_status.get(username, (self.tries, 0))
            if status[0] < 1 and time.time() < status[1]:
                # User got the password wrong within the last (self.lockTime) seconds
                if self.printdebug: self.printdebug("AUTH DEBUG wrong pw within last locktime")
                return self.denyForbidden()
            if status[0] < 1:
                if self.printdebug: self.printdebug("AUTH DEBUG wrong pw, user may retry")
                # User sent the wrong password, but more than (self.lockTime) seconds have passed, so give
                # them another try.  However, send a 401 header so user's browser prompts for a password
                # again.
                self.user_status[username] = (1, 0)
                return self.send401UnauthorizedResponse()
            if self.requestDigestValid(reqHeaderDict, web.ctx.environ['REQUEST_METHOD']):
                # User authenticated; forgive any past incorrect passwords and run the function we're decorating
                if self.printdebug: self.printdebug( "AUTH DEBUG auth succesful")
                self.user_status[username] = (self.tries, 0)
                arguments += (username,) #added by proycon
                return f(*arguments, **keywords)
            else:
                # User entered the wrong password.  Deduct one try, and lock account if necessary
                if self.printdebug: self.printdebug( "AUTH DEBUG wrong pw, one less try")
                self.user_status[username] = (status[0] - 1, time.time() + self.lockTime)
                self.logIncorrectPassword(username,  reqHeaderDict)
                return self.send401UnauthorizedResponse()
        return wrapper


    def logIncorrectPassword(self,  username,  reqHeaderDict):
        pass  # Do your own logging here


    def directiveProper(self,  reqHeaderDict, reqPath):
        """Verifies that the client's authentication header contained the required fields"""
        if self.urlprefix:
            if self.urlprefix[0] != '/':
                urlprefix = '/' + self.urlprefix
            if self.urlprefix[-1] == '/':
                urlprefix = self.urlprefix[:-1]
        else:
            urlprefix = ""

        for variable in ['username','realm','nonce','uri','response','cnonce','nc']:
            if variable not in reqHeaderDict:
                if self.printdebug: self.printdebug( "DEBUG directiveProper: missing " + variable)
                return False
        # IE doesn't send "opaque" and does not include GET parameters in the Digest field
        #standardsUncompliant = self.tolerateIE and ("MSIE" in web.ctx.environ.get('HTTP_USER_AGENT',""))
        standardsUncompliant = True #Support crappy (Microsoft) software by default, regardless of uyser agent.
        if standardsUncompliant:
            if '?' in reqHeaderDict['uri']:
                reqHeaderDict['uri'] = reqHeaderDict['uri'].split('?')[0]
            if '?' in reqPath:
                reqPath = reqPath.split('?')[0]


        if reqHeaderDict['realm'] != self.realm:
            if self.printdebug: self.printdebug( "DEBUG directiveProper: realm not matching got '" + reqHeaderDict['realm'] + "' expected '" + self.realm + "'")
            return False
        elif not (standardsUncompliant or reqHeaderDict.get('opaque','') == self.opaque):
            if self.printdebug: self.printdebug( "DEBUG directiveProper: got opaque '" + str(reqHeaderDict.get('opaque','')) + "' expected '" + str(self.opaque) + '"')
            return False
        elif len(reqHeaderDict['nc']) != 8:
            if self.printdebug: self.printdebug( "DEBUG directiveProper nc != 8")
            return False
        elif not (reqHeaderDict['uri'] == reqPath or reqHeaderDict['uri'] == urlprefix + reqPath):  # or (standardsUncompliant and "?" in reqPath and (reqPath.startswith(reqHeaderDict['uri']) or reqPath.startswith(urlprefix + reqHeaderDict['uri'])) )):
            if self.printdebug: self.printdebug( "DEBUG mismatch in request paths, got '" +  str(reqHeaderDict['uri']) + "' instead of '" + str(reqPath) + "'")
            if urlprefix:
                if self.printdebug: self.printdebug( "..or instead of '" + urlprefix + str(reqPath) + "'")
            return False

        return True

        #return reqHeaderDict['realm'] == self.realm \
        #    and (standardsUncompliant or reqHeaderDict.get('opaque','') == self.opaque) \
        #    and len(reqHeaderDict['nc']) == 8 \
        #    and (reqHeaderDict['uri'] == reqPath or (standardsUncompliant and "?" in reqPath and reqPath.startswith(reqHeaderDict['uri'])))


    def requestDigestValid(self, reqHeaderDict, reqMethod):
        """Checks to see if the client's request properly authenticates"""
        # Ask the application for the hash of A1 corresponding to this username and realm
        try:
            HA1 = self.getHA1(reqHeaderDict['username'], reqHeaderDict['realm'])
        except KeyError:
            # No such user
            return False
        qop = reqHeaderDict.get('qop','auth')
        A2 = "%s:%s" % (reqMethod, reqHeaderDict['uri'])
        # auth-int stuff would go here, but few browsers support it
        nonce = reqHeaderDict['nonce']
        # Calculate the response we should have received from the client
        correctAnswer = H("%s:%s" % (HA1, ":".join([nonce, reqHeaderDict['nc'], reqHeaderDict['cnonce'], qop, H(A2) ])))
        # Compare the correct response to what the client sent
        return reqHeaderDict['response'] == correctAnswer


    def send401UnauthorizedResponse(self,  stale=False):
        web.ctx.status = "401 Unauthorized"
        nonce = self.outstandingNonces.getNewNonce(self.nonceLife)
        challengeList = [ "realm=%s" % quoteIt(self.realm),
                                   self.domain and ('domain=%s' % quoteIt(" ".join(self.domain))) or '',
                                   'qop="auth",nonce=%s,opaque=%s' % tuple(map(quoteIt, [nonce, self.opaque])),
                                   stale and 'stale="true"' or '']
        web.header("WWW-Authenticate", "Digest " + ",".join(x for x in challengeList if x))
        web.header("Content-Type","text/html")
        if self.webpy2:
            print self.unauthHTML
            return None
        return self.unauthHTML


    def denyBadRequest(self,  info=""):
        """Sent when the authentication header doesn't conform with protocol"""
        web.header("Content-Type","text/html")
        web.ctx.status = "400 Bad Request"
        s1 = web.ctx.status + info
        if self.webpy2:
            print s1
            return None
        return s1


    def denyForbidden(self):
        """Sent when user has entered an incorrect password too many times"""
        web.ctx.status = "403 Forbidden"
        if self.webpy2:
            print self.unauthHTML
            return None
        return self.unauthHTML


    def _getValidAuthHeader(self):
        """returns valid dictionary of authorization header, or None"""
        requestHeader = web.ctx.environ.get('HTTP_AUTHORIZATION', None)
        if not requestHeader:
            raise MalformedAuthenticationHeader()
        if requestHeader[0:7] != "Digest ":
            raise MalformedAuthenticationHeader()
        reqHeaderDict = parseAuthHeader(requestHeader)
        if not self.directiveProper(reqHeaderDict, web.ctx.fullpath):
            raise MalformedAuthenticationHeader()
        return reqHeaderDict


    def logout(self):
        """Cause user's browser to stop sending correct authentication requests until user re-enters password"""
        try:
            reqHeaderDict = self._getValidAuthHeader()
        except MalformedAuthenticationHeader:
            return
        if len(reqHeaderDict.nonce) == 34:
            # First time: send a 401 giving the user the fake "logout" nonce
            web.ctx.status = "401 Unauthorized"
            nonce = "%032x" % random.getrandbits(136)
            challengeList = [ "realm=%s" % quoteIt(self.realm),
                               'qop="auth",nonce=%s,opaque=%s' % tuple(map(quoteIt, [nonce, self.opaque])),
                                'stale="true"']
            web.header("WWW-Authenticate", "Digest " + ",".join(x for x in challengeList if x))


    def authUserName(self):
        """Returns the HTTP username, or None if not logged in."""
        reqHeaderDict = self._getValidAuthHeader()
        return reqHeaderDict.username

def H(data):
    """Return a hex digest MD5 hash of the argument"""
    return md5(data).hexdigest()


def quoteIt(x):
    """Return the argument quoted, suitable for a quoted-string"""
    return '"%s"' % (x.replace("\\","\\\\").replace('"','\\"'))

## Code to parse the authentication header
parseAuthHeaderRE = re.compile(r"""
    (   (?P<varq>[a-z]+)="(?P<valueq>.+?)"(,|$)    )   # match variable="value", (terminated by a comma or end of line)
    |
    (   (?P<var>[a-z]+)=(?P<value>.+?)(,|$)    )          # match variable=value,  (same as above, but no quotes)
    """,  re.VERBOSE | re.IGNORECASE )
def parseAuthHeader(header):
    d = web.Storage()
    for m in parseAuthHeaderRE.finditer(header):
        g = m.groupdict()
        if g['varq'] and g['valueq']:
            d[g['varq']] = g['valueq'].replace(r'\"',  '"')
        elif g['var'] and g['value']:
            d[g['var']] = g['value']
    return d

class NonceMemory(dict):
    def getNewNonce(self,  lifespan = 180):
        while 1:
            nonce = "%034x" % random.getrandbits(136)  # a random 136-bit zero-padded lowercase hex string
            if nonce not in self:
                break
        self[nonce] = (time.time() + lifespan, 1)
        return nonce


    def nonceState(self, reqHeaderDict,  nonceSkip = 1):
        """ 1 = nonce valid, proceed; 2 = nonce totally invalid;  3 = nonce requires refreshing """
        nonce = reqHeaderDict.get('nonce', None)
        expTime, nCount = self.get(nonce, (0,0) )
        if expTime == 0:
            # Client sent some totally unknown nonce -- reject
            return 2
        try:
            incoming_nc = int((reqHeaderDict['nc']), 16)
        except ValueError:
            return 2  # the "nc" field was deformed (not hexadecimal); reject
        if expTime == 1 or nCount > 1000 or expTime < time.time() or incoming_nc - nCount > nonceSkip:
            # Client sent good nonce, but it is too old, or the count has gotten screwed up; give them a new one
            del self[nonce]
            return 3
        self[nonce] = (expTime, incoming_nc + 1)
        return 1
