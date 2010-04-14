#!/usr/bin/env python
#-*- coding:utf-8 -*-

import web


urls = ('/upload', 'Upload')
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    app.run()



class Upload:
    def GET(self):
        return """<html><head></head><body>
<form method="POST" enctype="multipart/form-data" action="">
<input type="file" name="myfile" />
<br/>
<input type="submit" />
</form>
</body></html>"""

    def POST(self):
        x = web.input(myfile={})
        #web.debug(x['myfile'].filename) # This is the filename
        #web.debug(x['myfile'].value) # This is the file contents
        f = open('/tmp/tst','wb')
        for line in x['myfile'].file:
            f.write(line)
        f.close()
        return "done"        
        #raise web.seeother('/upload')


