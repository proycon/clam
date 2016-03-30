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
import argparse

try:
    import clam
    CLAMDIR = os.path.abspath(clam.__path__[0])
except ImportError:
    print("ERROR: Unable to find CLAM. Did you install it properly? Is your PYTHONPATH or virtual environment correct?",file=sys.stderr)
    sys.exit(2)

from clam.common.data import VERSION

def main():
    parser = argparse.ArgumentParser(description="This tool sets up a new CLAM project for you. It generates a bunch of templates for you to use as basis. Replace 'system_id' with a short ID/name for your project that will be used internally and possibly in URLs; it will be used in various filenames, no spaces or other special characters allowed.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n','--name',type=str, help="A human-readable name. Shortcut option, can be also set in service configuration file later", action='store', required=False)
    parser.add_argument('-d','--dirprefix',type=str, help="Directory prefix, rather than in current working directory", action='store', default=os.getcwd(), required=False)
    parser.add_argument('-H','--hostname', type=str,help="The hostname used to access the webservice", action='store',required=False)
    parser.add_argument('-p','--port', type=int,help="The port number for the webservice", action='store',default=8080,required=False)
    parser.add_argument('-P','--pythonversion', type=str,help="Python version (2 or 3)", action='store',default='3',required=False)
    parser.add_argument('-u','--forceurl', type=str,help="The full URL to access the webservice", action='store',required=False)
    parser.add_argument('-U','--uwsgiport', type=int,help="UWSGI port to use for this webservice when deployed in prodution environments", action='store',default=8888,required=False)
    parser.add_argument('-f','--force',help="Force use of a directory which already exists", action='store_true',required=False)
    parser.add_argument('-v','--version',help="Version", action='version',version="CLAM version " + str(VERSION))
    parser.add_argument('sysid',type=str, help='System ID')
    args = parser.parse_args()


    if ' ' in args.sysid or '.' in args.sysid or '-' in args.sysid or ',' in args.sysid or ':' in args.sysid or ':' in args.sysid or '(' in args.sysid or ')' in args.sysid or '/' in args.sysid or "'" in args.sysid or '"' in args.sysid:
        print("Invalid characters in system ID. Only alphanumerics and underscores are allowed.",file=sys.stderr)
        sys.exit(2)

    for template in ('config/template.py','wrappers/template.py','wrappers/template.sh'):
        if not os.path.exists(os.path.join(CLAMDIR,template)):
            print("ERROR: Templates not found (Could not find " + os.path.join(CLAMDIR,template) +"). Unable to create new project",file=sys.stderr)
            sys.exit(2)

    dir = args.dirprefix + "/" + args.sysid

    if os.path.exists(dir):
        if 'force' not in args or not args.force:
            print("ERROR: Directory " +dir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project directory " + dir,file=sys.stderr)
        os.mkdir(dir)

    if not os.path.exists(dir+ "/__init__.py"):
        f = open(dir+ "/__init__.py",'w')
        f.close()

    if not os.path.exists(dir + '/' + args.sysid + '.py'):
        fin = io.open(CLAMDIR + '/config/template.py','r',encoding='utf-8')
        fout = io.open(dir + '/' + args.sysid + '.py','w',encoding='utf-8')
        for line in fin:
            if line == "SYSTEM_ID = \"\"\n":
                line =  "SYSTEM_ID = \"" + args.sysid + "\""
            elif 'name' in args and args.name and line[:13] == "SYSTEM_NAME =":
                line = "SYSTEM_NAME = \"" + args.name + "\"\n"
            elif 'hostname' in args and args.hostname and line[:7] == "#HOST =":
                line = "HOST = \"" + args.hostname+ "\"\n"
            elif 'port' in args and args.port and (line[:7] == "#PORT =" or line[:6] == "PORT ="):
                line = "PORT = \"" + str(args.port) + "\"\n"
            elif line[:6] == "ROOT =":
                line = "ROOT = \"" + dir + "/userdata\"\n"
            elif 'forceurl' in args and args.forceurl and line[:9] == '#FORCEURL':
                line = "FORCEURL = \"" + args.forceurl + "\"\n"
            elif line[:9] == "COMMAND =":
                line = "COMMAND = WEBSERVICEDIR + \"/" + args.sysid + "_wrapper.py $DATAFILE $STATUSFILE $OUTPUTDIRECTORY\"\n"
            elif line[:10] == "#COMMAND =":
                line = "#COMMAND = WEBSERVICEDIR + \"/" + args.sysid + "_wrapper.sh $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY $PARAMETERS\"\n"
            fout.write(line)
        fin.close()
        fout.close()
    else:
        print("WARNING: Service configuration file " + dir + '/' + args.sysid + ".py already seems to exists, courageously refusing to overwrite",file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(dir + '/' + args.sysid + '_wrapper.py'):
        shutil.copyfile(CLAMDIR + '/wrappers/template.py', dir + '/' + args.sysid + '_wrapper.py')
        os.chmod(dir + '/' + args.sysid + '_wrapper.py', 0o755)
    else:
        print("WARNING: System wrapper file " + dir + '/' + args.sysid + '_wrapper.py already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(dir + '/' + args.sysid + '_wrapper.sh'):
        shutil.copyfile(CLAMDIR + '/wrappers/template.sh', dir + '/' + args.sysid + '_wrapper.sh')
        os.chmod(dir + '/' + args.sysid + '_wrapper.sh', 0o755)
    else:
        print("WARNING: System wrapper file " + dir + '/' + args.sysid + '_wrapper.sh already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    with io.open(dir + '/'+args.sysid +'.wsgi','w',encoding='utf-8') as f:
        f.write("import sys\nsys.path.append(\"" + dir + "\")\nimport " + args.sysid + "\nimport clam.clamservice\napplication = clam.clamservice.run_wsgi(" +args.sysid+ ")")
    os.chmod(dir + '/' + args.sysid + '.wsgi', 0o755)

    with io.open(dir+'/nginx-withurlprefix-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Nginx example configuration using uwsgi, assuming your service is using URLPREFIX=\"{sysid}\", insert this in your server block in your nginx.conf
location /{sysid}/static {{ alias {clamdir}/static; }}
location = /{sysid} {{ rewrite ^ /{sysid}/; }}
location /{sysid} {{ try_files $uri @{sysid}; }}
location @{sysid} {{
    include uwsgi_params;
    uwsgi_pass 127.0.0.1:{uwsgiport};
}}""".format(sysid=args.sysid,clamdir=CLAMDIR, uwsgiport=args.uwsgiport))


    with io.open(dir+'/nginx-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Nginx example configuration using uwsgi, assuming your service runs at the root of the virtualhost, insert this in your server block in your nginx.conf
location /static {{ alias {clamdir}/static; }}
location / {{ try_files $uri @{sysid}; }}
location @{sysid} {{
    include uwsgi_params;
    uwsgi_pass 127.0.0.1:{uwsgiport};
}}""".format(sysid=args.sysid,clamdir=CLAMDIR, uwsgiport=args.uwsgiport))




    if args.pythonversion >= '3':
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
""".format(clamdir=CLAMDIR,sysid=args.sysid,uwsgiport=args.uwsgiport))

    with io.open(dir+'/apache-withurlprefix-sample.conf','w',encoding='utf-8') as f:
        f.write("""#Apache example configuration using mod-uwsgi-proxy, assuming your service runs at the virtualhost root, insert this in your VirtualHost in your Apache configuration

ProxyPass / uwsgi://127.0.0.1:{uwsgiport}/

Alias /static {clamdir}/static
<Directory {clamdir}/static/>
    Order deny,allow
    Allow from all
</Directory>
""".format(clamdir=CLAMDIR,sysid=args.sysid,uwsgiport=args.uwsgiport))

    with io.open(dir + '/startserver_production.sh','w',encoding='utf-8') as f:
        f.write("""#!/bin/bash
if [ ! -z $VIRTUAL_ENV ]; then
    uwsgi --plugin {uwsgiplugin} --virtualenv $VIRTUAL_ENV --socket 127.0.0.1:{uwsgiport} --chdir $VIRTUAL_ENV --wsgi-file {dir}/{sysid}.wsgi --logto {sysid}.uwsgi.log --log-date --log-5xx --master --processes 2 --threads 2 --need-app
else
    uwsgi --plugin {uwsgiplugin} --socket 127.0.0.1:{uwsgiport} --wsgi-file {dir}/{sysid}.wsgi --logto {sysid}.uwsgi.log --log-date --log-5xx --master --processes 2 --threads 2 --need-app
fi
""".format(dir=dir, sysid=args.sysid, uwsgiplugin=uwsgiplugin,pythonversion=args.pythonversion, uwsgiport=args.uwsgiport))
    os.chmod(dir + '/startserver_production.sh', 0o755)

    with io.open(dir + '/startserver_development.sh','w',encoding='utf-8') as f:
        f.write("""#!/bin/bash
if [ -z $PYTHONPATH ]; then
    export PYTHONPATH={dir}
else
    export PYTHONPATH={dir}:$PYTHONPATH
fi
clamservice -d {sysid}
""".format(dir=dir,sysid=args.sysid, pythonversion=args.pythonversion))
    os.chmod(dir + '/startserver_development.sh', 0o755)



    s = """
**Your new CLAM project has been set up!**

BUILD YOUR WEBSERVICE

To develop your webservice, edit your service configuration file
{dir}/{sysid}.py , and your system wrapper script {dir}/{sysid}_wrapper.py , or
{dir}/{sysid}_wrapper.sh if you prefer to use a simple shell script rather than
Python.  Consult the CLAM Documentation and/or instruction videos on
https://proycon.github.io/clam for further details on how to do this.

""".format(dir=dir,sysid=args.sysid)


    print(s,file=sys.stderr)

    if args.forceurl:
        url = args.forceurl
    else:
        url = "http://"
        if 'hostname' in args and args.hostname:
            url += args.hostname
        else:
            url += os.uname()[1]
        if 'port' in args and args.port != 80:
            url += ':' + str(args.port)
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
""".format(dir=dir,sysid=args.sysid)

    print( s2,file=sys.stderr)

    print( "\n(All of this information can be read again in the INSTRUCTIONS file)",file=sys.stderr)

    with io.open(dir + "/INSTRUCTIONS",'w',encoding='utf-8') as f:
        f.write(s + s2)

    if args.pythonversion >= '3':
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
