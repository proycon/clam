#!/usr/bin/env python
#-*- coding:utf-8 -*-

import web
import os
import glob
ROOT = "/tmp/clam/"

urls = (
    '/(.*)', 'FileHandler',
    '/', 'FileLister'
)
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    app.run()




class FileHandler:
    def GET(self, path):
        if os.path.isfile(ROOT + path): 
            for line in open(ROOT+path,'r'):
                yield line
        elif os.path.isdir(ROOT + path): 
            for f in glob.glob(ROOT + path + "/*"):
                yield os.path.basename(f)                
        else:
            raise web.webapi.NotFound()

    def POST(self, path):
        x = web.input(myfile={})
        #web.debug(x['myfile'].filename) # This is the filename
        #web.debug(x['myfile'].value) # This is the file contents
        f = open(ROOT + path,'w')
        for line in x['myfile'].file:
            f.write(line)
        f.close()
        return "done"        


