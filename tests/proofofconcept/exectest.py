#!/usr/bin/env python
#-*- coding:utf-8 -*-

import web
import os
import subprocess
basedir = "/var/clam"

urls = ('/exec', 'Exec')
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    app.run()



class Exec:
    def GET(self):
        if os.path.exists(".pid"):
            f = open('.pid')
            pid = int(f.read(1024))
            f.close()

            #check if process running?
            try:
                os.kill(pid, 0) #(doesn't really kill, but throws exception when process does not exist)
                f = open('.status')
                status = f.read(os.path.getsize('.status'))
                f.close()
                return status
            except:
                #if os.path.isfile(self.dir + "pid"):
                #    os.path.remove(self.dir + "pid")
                os.unlink('.pid')
                return "Done"                   
        else:
            return """<html><head></head><body>
<form method="POST" action"">
<input type="submit" value="start" />
</form>
</body></html>"""

    def POST(self):
        """Start a remote process"""
        cmd = ["./test.sh"]
        process = subprocess.Popen(cmd)		
        f = open('.pid','w')
        f.write(str(process.pid))
        f.close()
        return "Started"


