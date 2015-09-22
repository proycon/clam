#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language Studies
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################


from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import io
import shutil

try:
    import clam
    CLAMDIR = os.path.abspath(clam.__path__[0])
except ImportError:
    print("ERROR: Unable to find CLAM. Did you install it properly? Is your PYTHONPATH or virtual environment correct?",file=sys.stderr)
    sys.exit(2)

import getopt

def usage():
    print("Syntax: clamnewproject system_id [options]",file=sys.stderr)
    print("Description: This tool sets up a new CLAM project for you. It generates a bunch of templates for you to use as basis. Replace 'system_id' with a short ID/name for your project that will be used internally and possibly in URLs; it will be used in various filenames, no spaces or other special characters allowed.",file=sys.stderr)
    print("Options:",file=sys.stderr)
    print("\t-d [dir]      - Directory prefix, rather than in current working directory",file=sys.stderr)
    print("\t-f            - Force use of a directory that already exists",file=sys.stderr)
    print("\t-h            - This help message",file=sys.stderr)
    print("Configuration shortcuts:",file=sys.stderr)
    print("\t-n [name]     - A human-readable name. Shortcut option, can be also set in service configuration file later.",file=sys.stderr)
    print("\t-H [hostname] - Hostname. Shortcut option, can be also set in service configuration file later. ",file=sys.stderr)
    print("\t-p [port]     - Port.  Shortcut option, can be also set in service configuration file later.",file=sys.stderr)
    print("\t-u [url]      - Force URL. Shortcut option, can be also set in service configuration file later.",file=sys.stderr)
    print("\t-U [uwsgiport]- UWSGI port to use for this webservice when deployed in production environments (default: 8888).",file=sys.stderr)


def main():
    if len(sys.argv) < 2 or sys.argv[1][0] == '-':
        usage()
        sys.exit(1)

    sysid = sys.argv[1]
    if ' ' in sysid or '.' in sysid or '-' in sysid or ',' in sysid or ':' in sysid or ':' in sysid or '(' in sysid or ')' in sysid or '/' in sysid or "'" in sysid or '"' in sysid:
        print("Invalid characters in system ID. Only alphanumerics and underscores are allowed.",file=sys.stderr)
        sys.exit(2)


    HOST = FORCEURL = None
    PORT = 8080
    dirprefix = os.getcwd()
    force = False
    name = ""
    pythonversion = '3'
    uwsgiport ='8888'

    try:
        opts, args = getopt.getopt(sys.argv[2:], "hd:cH:p:u:fn:")
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-d':
            dirprefix = a
        elif o == '-H':
            HOST = a
        elif o == '-p':
            PORT = int(a)
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-u':
            FORCEURL = a
        elif o == '-U':
            uwsgiport = a
        elif o == '-f':
            force = True
        elif o == '-n':
            name = a
        elif o == '-P':
            pythonversion = a
        else:
            usage()
            print("ERROR: Unknown option: ", o)
            sys.exit(2)




    if not os.path.exists(CLAMDIR + '/config/template.py') or not os.path.exists(CLAMDIR + '/wrappers/template.sh') or not os.path.exists(CLAMDIR + '/wrappers/template.py'):
        print("ERROR: Templates not found. Unable to create new project",file=sys.stderr)
        sys.exit(2)

    dir = dirprefix + "/" +sysid

    if os.path.exists(dir):
        if not force:
            print("ERROR: Directory " +dir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project directory " + dir,file=sys.stderr)
        os.mkdir(dir)

    if not os.path.exists(dir+ "/__init__.py"):
        f = open(dir+ "/__init__.py",'w')
        f.close()

    if not os.path.exists(dir + '/' + sysid + '.py'):
        fin = io.open(CLAMDIR + '/config/template.py','r',encoding='utf-8')
        fout = io.open(dir + '/' + sysid + '.py','w',encoding='utf-8')
        for line in fin:
            if line == "SYSTEM_ID = \"\"\n":
                line =  "SYSTEM_ID = \"" + sysid + "\""
            elif name and line[:13] == "SYSTEM_NAME =":
                line = "SYSTEM_NAME = \"" + name + "\"\n"
            elif HOST and line[:7] == "#HOST =":
                line = "HOST = \"" + HOST + "\"\n"
            elif PORT and (line[:7] == "#PORT =" or line[:6] == "PORT ="):
                line = "PORT = \"" + str(PORT) + "\"\n"
            elif line[:6] == "ROOT =":
                line = "ROOT = \"" + dir + "/userdata\"\n"
            elif FORCEURL and line[:9] == '#FORCEURL':
                line = "FORCEURL = \"" + FORCEURL + "\"\n"
            elif line[:9] == "COMMAND =":
                line = "COMMAND = WEBSERVICEDIR + \"/" + sysid + "_wrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY\"\n"
            elif line[:10] == "#COMMAND =":
                line = "#COMMAND = WEBSERVICEDIR + \"/" + sysid + "_wrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS\"\n"
            fout.write(line)
        fin.close()
        fout.close()
    else:
        print("WARNING: Service configuration file " + dir + '/' + sysid + ".py already seems to exists, courageously refusing to overwrite",file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(dir + '/' + sysid + '_wrapper.py'):
        shutil.copyfile(CLAMDIR + '/wrappers/template.py', dir + '/' + sysid + '_wrapper.py')
        os.chmod(dir + '/' + sysid + '_wrapper.py', 0o755)
    else:
        print("WARNING: System wrapper file " + dir + '/' + sysid + '_wrapper.py already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(dir + '/' + sysid + '_wrapper.sh'):
        shutil.copyfile(CLAMDIR + '/wrappers/template.sh', dir + '/' + sysid + '_wrapper.sh')
        os.chmod(dir + '/' + sysid + '_wrapper.sh', 0o755)
    else:
        print("WARNING: System wrapper file " + dir + '/' + sysid + '_wrapper.sh already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    with io.open(dir + '/'+sysid +'.wsgi','w',encoding='utf-8') as f:
        f.write("import sys\nsys.path.append(\"" + dir + "\")\nimport " + sysid + "\nimport clam.clamservice\napplication = clam.clamservice.run_wsgi(" +sysid+ ")")
    os.chmod(dir + '/' + sysid + '.wsgi', 0o755)

    with io.open(dir+'/nginx-withurlprefix-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Nginx example configuration using uwsgi, assuming your service is using URLPREFIX=\"{sysid}\", insert this in your server block in your nginx.conf
location /{sysid}/static {{ alias {clamdir}/static; }}
location = /{sysid} {{ rewrite ^ /{sysid}/; }}
location /{sysid} {{ try_files $uri @{sysid}; }}
location @{sysid} {{
    include uwsgi_params;
    uwsgi_pass 127.0.0.1:{uwsgiport};
}}""".format(sysid=sysid,clamdir=CLAMDIR, uwsgiport=uwsgiport))


    with io.open(dir+'/nginx-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Nginx example configuration using uwsgi, assuming your service runs at the root of the virtualhost, insert this in your server block in your nginx.conf
location /static {{ alias {clamdir}/static; }}
location / {{ try_files $uri @{sysid}; }}
location @{sysid} {{
    include uwsgi_params;
    uwsgi_pass 127.0.0.1:{uwsgiport};
}}""".format(sysid=sysid,clamdir=CLAMDIR, uwsgiport=uwsgiport))




    if pythonversion >= '3':
        uwsgiplugin = 'python3'
    else:
        uwsgiplugin = 'python'

    with io.open(dir+'/apache-withurlprefix-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Apache example configuration using mod-uwsgi-proxy, assuming your service is using URLPREFIX=\"{sysid}\", insert this in your VirtualHost in your Apache configuration

ProxyPass /{sysid} uwsgi://127.0.0.1:{uwsgiport}/

Alias /{sysid}/static {clamdir}/static
<Directory {clamdir}/static/>
    Order deny,allow
    Allow from all
</Directory>
""".format(clamdir=CLAMDIR,sysid=sysid,uwsgiport=uwsgiport))

    with io.open(dir+'/apache-withurlprefix-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Apache example configuration using mod-uwsgi-proxy, assuming your service runs at the virtualhost root, insert this in your VirtualHost in your Apache configuration

ProxyPass / uwsgi://127.0.0.1:{uwsgiport}/

Alias /static {clamdir}/static
<Directory {clamdir}/static/>
    Order deny,allow
    Allow from all
</Directory>
""".format(clamdir=CLAMDIR,sysid=sysid,uwsgiport=uwsgiport))

    with io.open(dir + '/startserver_production.sh','w',encoding='utf-8') as f:
        f.write("""#!/bin/bash
if [ ! -z $VIRTUAL_ENV ]; then; 
    uwsgi --plugin {uwsgiplugin} --virtualenv $VIRTUAL_ENV --socket 127.0.0.1:{uwsgiport} --chdir $VIRTUAL_ENV --wsgi-file {dir}/{sysid}.wsgi --logto {sysid}.uwsgi.log --log-date --log-5xx --master --processes 2 --threads 2 --need-app
else 
    uwsgi --plugin {uwsgiplugin} --socket 127.0.0.1:{uwsgiport} --wsgi-file {dir}/{sysid}.wsgi --logto {sysid}.uwsgi.log --log-date --log-5xx --master --processes 2 --threads 2 --need-app
fi
""".format(dir=dir, sysid=sysid, uwsgiplugin=uwsgiplugin,pythonversion=pythonversion, uwsgiport=uwsgiport))
    os.chmod(dir + '/startserver_production.sh', 0o755)

    with io.open(dir + '/startserver_development.sh','w',encoding='utf-8') as f:
        f.write("""#!/bin/bash
if [ -z $PYTHONPATH ]; then
    export PYTHONPATH={dir}
else
    export PYTHONPATH={dir}:$PYTHONPATH
fi
clamservice {sysid}
""".format(dir=dir,sysid=sysid, pythonversion=pythonversion))
    os.chmod(dir + '/startserver_development.sh', 0o755)



    s = """
**Your new CLAM project has been set up!**

BUILD YOUR WEBSERVICE

To develop your webservice, edit your service configuration file
{dir}/{sysid}.py , and your system wrapper script {dir}/{sysid}_wrapper.py , or
{dir}/{sysid}_wrapper.sh if you prefer to use a simple shell script rather than
Python.  Consult the CLAM Documentation and/or instruction videos on
https://proycon.github.io/clam for further details on how to do this.

""".format(dir=dir,sysid=sysid)


    print(s,file=sys.stderr)

    if FORCEURL:
        url = FORCEURL
    else:
        url = "http://"
        if HOST:
            url += HOST
        else:
            url += os.uname()[1]
        if PORT and PORT != 80:
            url += ':' + str(PORT)
        url += '/'

    s2 = """
START YOUR WEBSERVICE
-------------------------

Whilst you are in the process of building your CLAM webservice, you can start
and test your webservice using the built-in development webserver, start it
with ./startserver_development.sh . This takes care of any installation as well.
Once started, you can point your browser to the URL advertised by this script.


DEPLOYING YOUR WEBSERVICE (for system administrators)
-------------------------------------------------------

For production use, we recommend using uwsgi in combination with a webserver
such as Apache (with mod_uwsgi_proxy), or nginx. A wsgi script and sample
configuration has been generated  as a starting point. Use the
./startserver_production.sh script to launch CLAM using uwsgi.
""".format(dir=dir,sysid=sysid)

    print( s2,file=sys.stderr)

    print( "\n(All of this information can be read again in the INSTRUCTIONS file)",file=sys.stderr)

    with io.open(dir + "/INSTRUCTIONS",'w',encoding='utf-8') as f:
        f.write(s + s2)

    if pythonversion >= '3':
        pip = 'pip3'
    else:
        pip = 'pip'

    with io.open(dir + "/INSTALL",'w',encoding='utf-8') as f:
        f.write("""Install CLAM from the Python package index with: 

 $ {pip} install clam

You may need to use sudo for global installation. We recommend the use of Python virtual environment.

The webservice runs from this directory directly. No further installation is necessary.""".format(pip=pip))


if __name__ == "__main__":
    main()
