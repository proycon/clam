#!/usr/bin/python

import web
assert web.__version__.startswith('0.3')
import ..digestauth

# You need a function that takes a username and returns
# an MD5 password hash of 'username:realm:password.'
# Use a database, not a hard-coded dictionary like this.
def userPasswordHash(user, realm):
    users = { 'guest' : digestauth.H('guest:wall:guest') }
    return users[user]

# Create your decorator
auth = digestauth.auth(userPasswordHash, realm='wall')

urls = ( '/write', 'write',
         '/logout',  'logout', 
         '/',      'index')

wallList = []

# Anyone can see the index, so decorator is not used here
class index(object):
    def GET(self):
        html = '<html><head><title>wall</title></head><body>'
        html += '<br/>'.join(web.websafe(x) for x in wallList)
        html += """<br/><form action="/write" method="post">
                   <input name="written"/><input type="submit" />
                   <p><a href="/logout">Logout</a></p>
                   </body></html>"""
        return html

# Only authenticated users can write, so put @auth before the POST method
class write(object):
    @auth  
    def POST(self):
        wallList.append( auth.authUserName() + " says: " + web.input()['written'] )
        raise web.seeother('/')

# An imperfect solution to the logout problem
class logout(object):
    def GET(self):
        auth.logout()
        return "You are logged out."

web.application(urls, globals()).run()


