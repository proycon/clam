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
    parser.add_argument('-p','--port', type=int,help="The port number for the HTTP webservice", action='store',default=8080,required=False)
    parser.add_argument('-P','--pythonversion', type=str,help="Python version (2 or 3)", action='store',default='3',required=False)
    parser.add_argument('-u','--forceurl', type=str,help="The full URL to access the webservice", action='store',required=False)
    parser.add_argument('-U','--uwsgiport', type=int,help="UWSGI port to use for this webservice when deployed in production environments", action='store',default=8888,required=False)
    parser.add_argument('-f','--force',help="Force use of a directory which already exists", action='store_true',required=False)
    parser.add_argument('--noninteractive',help="Non-interactive mode, don't ask questions", action='store_true',required=False)
    parser.add_argument('-v','--version',help="Version", action='version',version="CLAM version " + str(VERSION))
    parser.add_argument('sysid',type=str, help='System ID')
    args = parser.parse_args()

    createvenv = False
    if 'CONDA_PREFIX' in os.environ:
        print("NOTICE: Anaconda detected")
    elif 'VIRTUAL_ENV' not in os.environ and not args.noninteractive:
        print("WARNING: You are not inside a Python Virtual Environment, using one is strongly recommended")
        yn = None
        while yn.strip().lower() not in ('y','yes','n','no'):
            if sys.version <= '3':
                yn = raw_input("Do you want us to create one for you? (assuming virtualenv is installed) [yn]").strip()
            else:
                yn = input("Do you want us to create one for you? (assuming virtualenv is installed) [yn]").strip()
            createvenv = yn.strip().lower() in ("y","yes")



    if ' ' in args.sysid or '.' in args.sysid or '-' in args.sysid or ',' in args.sysid or ':' in args.sysid or ':' in args.sysid or '(' in args.sysid or ')' in args.sysid or '/' in args.sysid or "'" in args.sysid or '"' in args.sysid:
        print("Invalid characters in system ID. Only alphanumerics and underscores are allowed.",file=sys.stderr)
        sys.exit(2)

    for template in ('config/template.py','wrappers/template.py','wrappers/template.sh', 'config/setup_template.py'):
        if not os.path.exists(os.path.join(CLAMDIR,template)):
            print("ERROR: Templates not found (Could not find " + os.path.join(CLAMDIR,template) +"). Unable to create new project",file=sys.stderr)
            sys.exit(2)

    rootdir = os.path.join(args.dirprefix, args.sysid)

    if os.path.exists(rootdir):
        if 'force' not in args or not args.force:
            print("ERROR: Directory " +rootdir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project directory " + rootdir,file=sys.stderr)
        os.mkdir(rootdir)

    if createvenv:
        os.chdir(rootdir)
        r = os.system("virtualenv --python=python" + str(args.pythonversion) + " env")
        if r != 0:
            print("ERROR: Unable to create virtual environment",file=sys.stderr)

    sourcedir = os.path.join(rootdir, args.sysid)
    if os.path.exists(sourcedir):
        if 'force' not in args or not args.force:
            print("ERROR: Directory " +sourcedir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project directory " + sourcedir,file=sys.stderr)
        os.mkdir(sourcedir)


    if not os.path.exists(os.path.join(sourcedir, "__init__.py")):
        f = open(os.path.join(sourcedir, "__init__.py"),'w')
        f.close()

    if not os.path.exists(os.path.join(sourcedir, args.sysid + '.py')):
        fin = io.open(os.path.join(CLAMDIR, 'config/template.py'),'r',encoding='utf-8')
        fout = io.open(os.path.join(sourcedir, args.sysid + '.py'),'w',encoding='utf-8')
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
                line = "ROOT = \"" + os.path.join(rootdir, "userdata") + "\"\n"
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
        print("WARNING: Service configuration file " + sourcedir + '/' + args.sysid + ".py already seems to exists, courageously refusing to overwrite",file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(os.path.join(rootdir, 'setup_template.py')):
        fin = io.open(os.path.join(CLAMDIR, 'config/setup_template.py'),'r',encoding='utf-8')
        fout = io.open(os.path.join(rootdir, 'setup.py'),'w',encoding='utf-8')
        for line in fin:
            line = line.replace("SYSTEM_ID", args.sysid)
            print(line,end="",file=fout)
        fout.close()
        fin.close()

    if not os.path.exists(os.path.join(sourcedir, args.sysid + '_wrapper.py')):
        shutil.copyfile(os.path.join(CLAMDIR, 'wrappers','template.py'), os.path.join(sourcedir, args.sysid + '_wrapper.py'))
        os.chmod(os.path.join(sourcedir, args.sysid + '_wrapper.py'), 0o755)
    else:
        print("WARNING: System wrapper file " + sourcedir + '/' + args.sysid + '_wrapper.py already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(os.path.join(sourcedir, args.sysid + '_wrapper.sh')):
        shutil.copyfile(os.path.join(CLAMDIR, 'wrappers','template.sh'), os.path.join(sourcedir, args.sysid + '_wrapper.sh'))
        os.chmod(os.path.join(sourcedir, args.sysid + '_wrapper.sh'), 0o755)
    else:
        print("WARNING: System wrapper file " + sourcedir + '/' + args.sysid + '_wrapper.sh already seems to exists, defiantly refusing to overwrite',file=sys.stderr)
        sys.exit(2)

    with io.open(os.path.join(sourcedir, args.sysid +'.wsgi'),'w',encoding='utf-8') as f:
        f.write("from " + args.sysid + " import " + args.sysid + "\nimport clam.clamservice\napplication = clam.clamservice.run_wsgi(" +args.sysid+ ")")
    os.chmod(os.path.join(sourcedir, args.sysid + '.wsgi'), 0o755)

    with io.open(os.path.join(rootdir,'nginx-withurlprefix.conf'),'w',encoding='utf-8') as f:
        f.write("""#Nginx example configuration using uwsgi, assuming your service is using URLPREFIX=\"{sysid}\", include this in your server block in your nginx.conf
location /{sysid}/static {{ alias {clamdir}/static; }}
location = /{sysid} {{ rewrite ^ /{sysid}/; }}
location /{sysid} {{ try_files $uri @{sysid}; }}
location @{sysid} {{
    include uwsgi_params;
    uwsgi_pass 127.0.0.1:{uwsgiport};
}}""".format(sysid=args.sysid,clamdir=CLAMDIR, uwsgiport=args.uwsgiport))


    with io.open(os.path.join(rootdir,'nginx.conf'),'w',encoding='utf-8') as f:
        f.write("""#Nginx example configuration using uwsgi (assuming your service runs at the root of the server!) include this from your server block in your nginx.conf
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

    with io.open(os.path.join(rootdir,'apache-withurlprefix.conf'),'w',encoding='utf-8') as f:
        f.write("""#Apache example configuration using mod-uwsgi-proxy, assuming your service is using URLPREFIX=\"{sysid}\", include this from your VirtualHost in your Apache configuration

ProxyPass /{sysid} uwsgi://127.0.0.1:{uwsgiport}/

#You will likely need to adapt the reference to path {clamdir} if you move this to another system
Alias /{sysid}/static {clamdir}/static
<Directory {clamdir}/static/>
    Order deny,allow
    Allow from all
</Directory>
""".format(clamdir=CLAMDIR,sysid=args.sysid,uwsgiport=args.uwsgiport))

    with io.open(os.path.join(rootdir,'apache.conf'),'w',encoding='utf-8') as f:
        f.write("""#Apache example configuration using mod-uwsgi-proxy (assuming your service runs at the virtualhost root!) insert this in your VirtualHost in your Apache configuration

ProxyPass / uwsgi://127.0.0.1:{uwsgiport}/

#You will likely need to adapt the reference to path {clamdir} if you move this to another system
Alias /static {clamdir}/static
<Directory {clamdir}/static/>
    Order deny,allow
    Allow from all
</Directory>
""".format(clamdir=CLAMDIR,sysid=args.sysid,uwsgiport=args.uwsgiport))


    with io.open(os.path.join(rootdir, 'startserver_development.sh'),'w',encoding='utf-8') as f:
        f.write("""#!/bin/bash
if [ ! -z "$VIRTUAL_ENV" ]; then
    python setup.py develop
else
    echo "No virtual environment detected, you have to take care of  running setup.py install or setup.py develop yourself!">&2
fi
clamservice -d {sysid}.{sysid}
""".format(dir=dir,sysid=args.sysid, pythonversion=args.pythonversion))
    os.chmod(os.path.join(rootdir, 'startserver_development.sh'), 0o755)

    if 'VIRTUAL_ENV' in os.environ:
        virtualenv = os.environ['VIRTUAL_ENV']
    elif createvenv:
        virtualenv = os.path.join(rootdir, "env")
    else:
        virtualenv = None

    if args.hostname:
        hostname = args.hostname
    else:
        hostname = os.uname()[1]
    with io.open(os.path.join(sourcedir,args.sysid + '.' + hostname + '.yml'),'w',encoding='utf-8') as f:
        f.write("""
host: {hostname}
root: {rootdir}/userdata
port: {port}
""".format(hostname=hostname,rootdir=rootdir,port=args.port))
    if args.forceurl:
        with io.open(os.path.join(sourcedir, args.sysid + '.' + hostname + '.yml'),'a',encoding='utf-8') as f:
            f.write("forceurl: {forceurl}".format(forceurl=args.forceurl))


    with io.open(os.path.join(rootdir,args.sysid + '.' + hostname + '.ini'),'w',encoding='utf-8') as f:
        f.write("""[uwsgi]
socket = 127.0.0.1:{uwsgiport}
master = true
#plugins = {uwsgiplugin},logfile
logger = file:{rootdir}/{sysid}.uwsgi.log
mount = /={sourcedir}/{sysid}.wsgi
#if you configured a URL prefix then you may want to use this instead:
#mount = /{sysid}={sourcedir}/{sysid}.wsgi
processes = 2
threads = 2
#enable this for nginx:
#manage-script-name = yes
""".format(sourcedir=sourcedir, rootdir=rootdir,sysid=args.sysid, uwsgiplugin=uwsgiplugin,pythonversion=args.pythonversion, uwsgiport=args.uwsgiport, virtual_env=os.environ['VIRTUAL_ENV']))
    if virtualenv:
        with io.open(os.path.join(rootdir,args.sysid + '.' + hostname + '.ini'),'a',encoding='utf-8') as f:
            f.write("virtualenv = " + virtualenv + "\n")
            f.write("chdir = " + virtualenv + "\n")

    with io.open(os.path.join(rootdir, 'startserver_production.sh'),'w',encoding='utf-8') as f:
        f.write("""#!/bin/bash
if [ ! -z "$VIRTUAL_ENV" ]; then
    python setup.py install
else
    echo "No virtual environment detected, you have to take care of running setup.py install or setup.py develop yourself!">&2
fi
HOSTNAME=$(hostname)
echo "Detected hostname: $HOSTNAME">&2
if [ ! -f "{sysid}.$HOSTNAME.ini" ]; then
        echo "Expected uwsgi configuration {sysid}.$HOSTNAME.ini not found. Did you make one for the host you are running on?">&2
        exit 2
fi
uwsgi {sysid}.$HOSTNAME.ini || cat {sysid}.uwsgi.log
""".format(sourcedir=sourcedir, sysid=args.sysid, uwsgiplugin=uwsgiplugin,pythonversion=args.pythonversion, uwsgiport=args.uwsgiport))
    os.chmod(os.path.join(rootdir , 'startserver_production.sh'), 0o755)

    with io.open(os.path.join(rootdir, '.gitignore'),'w',encoding='utf-8') as f:
        f.write("""
__pycache__/
*.py[cod]
build/
dist/
userdata/
*.log
*.egg
*.egg-info
env/
*.bak
*~
.DS_Store
._*
""")


    s = """
**Your new CLAM project has been set up!**

DEVELOP YOUR WEBSERVICE
----------------------------

To develop your webservice, edit your service configuration file ``{sourcedir}/{sysid}.py`` , the host specific
configuration file ``{sourcedir}/{sysid}.$HOSTNAME.yml``, and your system wrapper script
``{sourcedir}/{sysid}_wrapper.py`` (or ``{sourcedir}/{sysid}_wrapper.sh`` if you prefer to use a simple shell script
rather than Python).

Keep host-specific settings out of the service configuration file and instead put it in the respective
config.$HOSTNAME.yml file that is automatically included by the service configuration. Create a new one for each host
you plan to deploy this webservice on.

Consult the CLAM Documentation and/or instruction videos on
https://proycon.github.io/clam for further details on how to do this.

Also don't forget to edit the metadata in the setup script ``{rootdir}/setup.py`` and run ``python setup.py install`` to install the webservice after you made any changes (the start scripts provided will do so automatically for you).
""".format(sourcedir=sourcedir,rootdir=rootdir,sysid=args.sysid)


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
with ``./startserver_development.sh`` . This takes care of any installation as well.
Once started, you can point your browser to the URL advertised by this script.


DEPLOYING YOUR WEBSERVICE (for system administrators)
-------------------------------------------------------

For production use, we recommend using uwsgi in combination with a webserver
such as Apache (with mod_uwsgi_proxy), or nginx. A uwsgi configuration has been generated ({sysid}.$HOSTNAME.ini); it is specific
to the host you deploy the webservice on. This in turn loads the wsgi script ({sysid}.wsgi), which loads your webservice.

Sample configurations for nginx and Apache have been generated as a starting point, add these to your server and then use the
``./startserver_production.sh`` script to launch CLAM using uwsgi.

VERSION CONTROL
-----------------

We *strongly* recommend you to put {rootdir} and everything inside under version control (e.g. git).
To create a new git repository::

    cd {rootdir}
    git init
    git add *
    git commit -m "generated by clamnewproject"

VIRTUAL ENVIRONMENT
--------------------

We strongly recommend the use of a Python virtual environment for your CLAM webservice, both in development and in production.
""".format(rootdir=rootdir,sysid=args.sysid)

    print( s2,file=sys.stderr)

    print( "\n(All of this information can be read again in the INSTRUCTIONS.rst file)",file=sys.stderr)

    with io.open(os.path.join(rootdir, "INSTRUCTIONS.rst"),'w',encoding='utf-8') as f:
        f.write(s + s2)

    if args.pythonversion >= '3':
        pip = 'pip3'
    else:
        pip = 'pip'

    with io.open(os.path.join(rootdir,"INSTALL"),'w',encoding='utf-8') as f:
        f.write("""Install CLAM from the Python package index with:

 $ {pip} install clam

Install the webservice:

 $ python setup.py install

You may need to use sudo for global installation. We recommend the use of a Python virtual environment.

The webservice runs from this directory directly. No further installation is necessary.""".format(pip=pip))


if __name__ == "__main__":
    main()
