#!/usr/bin/env python3
#-*- coding:utf-8 -*-

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Webservice --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language and Speech Technology, Radboud University Nijmegen
#       & KNAW Humanities Cluster
#
#       Licensed under GPLv3
#
###############################################################


import sys
import os
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
    parser.add_argument('-H','--hostname', type=str,help="The hostname used to access the webservice", action='store',required=False)
    parser.add_argument('-p','--port', type=int,help="The port number for the HTTP webservice during development", action='store',default=8080,required=False)
    parser.add_argument('-P','--pythonversion', type=str,help="Explicit python version, in case you have multiple installed. Note that python 2 is not supported!", action='store',default='3',required=False)
    parser.add_argument('-f','--force',help="Force use of a directory which already exists", action='store_true',required=False)
    parser.add_argument('--noninteractive',help="Non-interactive mode, don't ask questions", action='store_true',required=False)
    parser.add_argument('-v','--version',help="Version", action='version',version="CLAM version " + str(VERSION))
    parser.add_argument('sysid',type=str, help='System ID, an internal identifier for your project')
    args = parser.parse_args()

    createvenv = False
    if 'CONDA_PREFIX' in os.environ:
        print("NOTICE: Anaconda detected", file=sys.stderr)
    elif 'VIRTUAL_ENV' not in os.environ and not args.noninteractive:
        print("WARNING: You are not inside a Python Virtual Environment, using one is strongly recommended", file=sys.stderr)
        yn = None
        while yn is None or yn.strip().lower() not in ('y','yes','n','no'):
            yn = input("Do you want us to create one for you? [yn]").strip()
            createvenv = yn.strip().lower() in ("y","yes")



    if ' ' in args.sysid or '.' in args.sysid or '-' in args.sysid or ',' in args.sysid or ':' in args.sysid or ':' in args.sysid or '(' in args.sysid or ')' in args.sysid or '/' in args.sysid or "'" in args.sysid or '"' in args.sysid:
        print("Invalid characters in system ID. Only alphanumerics and underscores are allowed.",file=sys.stderr)
        sys.exit(2)

    for template in ('config/template.py','wrappers/template.py','wrappers/template.sh', 'config/setup_template.py'):
        if not os.path.exists(os.path.join(CLAMDIR,template)):
            print("ERROR: Templates not found (Could not find " + os.path.join(CLAMDIR,template) +"). Unable to create new project",file=sys.stderr)
            sys.exit(2)

    rootdir = os.path.join(os.getcwd(), args.sysid)

    if os.path.exists(rootdir):
        if 'force' not in args or not args.force:
            print("ERROR: Directory " +rootdir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project root directory " + rootdir,file=sys.stderr)
        os.mkdir(rootdir)

    if createvenv:
        os.chdir(rootdir)
        if os.system("which virtualenv") == 0:
            r = os.system("virtualenv --python=python" + str(args.pythonversion) + " env")
            if r != 0:
                print("ERROR: Unable to create virtual environment",file=sys.stderr)
        else:
            r = os.system("python" + str(args.pythonversion) + " -m venv env")
            if r != 0:
                print("ERROR: Unable to create virtual environment",file=sys.stderr)

    sourcedir = os.path.join(rootdir, args.sysid)
    if os.path.exists(sourcedir):
        if 'force' not in args or not args.force:
            print("ERROR: Directory " +sourcedir + " already exists.. Unable to make new CLAM project. Add -f (force) if you want to continue nevertheless ",file=sys.stderr)
            sys.exit(2)
    else:
        print("Making project source directory " + sourcedir,file=sys.stderr)
        os.mkdir(sourcedir)


    if not os.path.exists(os.path.join(sourcedir, "__init__.py")):
        f = open(os.path.join(sourcedir, "__init__.py"),'w')
        f.close()

    if not os.path.exists(os.path.join(sourcedir, args.sysid + '.py')):
        fin = open(os.path.join(CLAMDIR, 'config/template.py'),'r',encoding='utf-8')
        fout = open(os.path.join(sourcedir, args.sysid + '.py'),'w',encoding='utf-8')
        for line in fin:
            if line == "SYSTEM_ID = \"\"\n":
                line =  "SYSTEM_ID = \"" + args.sysid + "\""
            elif 'name' in args and args.name and line[:13] == "SYSTEM_NAME =":
                line = "SYSTEM_NAME = \"" + args.name + "\"\n"
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

    if not os.path.exists(os.path.join(rootdir, 'setup.py')):
        fin = open(os.path.join(CLAMDIR, 'config/setup_template.py'),'r',encoding='utf-8')
        fout = open(os.path.join(rootdir, 'setup.py'),'w',encoding='utf-8')
        for line in fin:
            line = line.replace("SYSTEM_ID", args.sysid)
            print(line,end="",file=fout)
        fout.close()
        fin.close()
        os.chmod(os.path.join(rootdir, 'setup.py'), 0o755)

    if not os.path.exists(os.path.join(rootdir, 'MANIFEST.in')):
        with open(os.path.join(rootdir, 'MANIFEST.in'),'w',encoding='utf-8') as fout:
            fout.write("""include README*
include {sysid}/*.py
include {sysid}/*.sh
include {sysid}/*.wsgi
include {sysid}/*.yml
""".format(sysid=args.sysid))

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

    with open(os.path.join(sourcedir, args.sysid +'.wsgi'),'w',encoding='utf-8') as f:
        f.write("from " + args.sysid + " import " + args.sysid + "\nimport clam.clamservice\napplication = clam.clamservice.run_wsgi(" +args.sysid+ ")")
    os.chmod(os.path.join(sourcedir, args.sysid + '.wsgi'), 0o755)


    with open(os.path.join(rootdir, 'startserver_development.sh'),'w',encoding='utf-8') as f:
        f.write("""#!/bin/sh
set -e
if [ -n "$VIRTUAL_ENV" ]; then
    pip install -e .
else
    if [ -d env ]; then
        . env/bin/activate
        pip install -e .
    else
        echo "No virtual environment detected, you have to take care of running python setup.py install or setup.py develop yourself!">&2
    fi 
fi
clamservice -d {sysid}.{sysid}
""".format(dir=dir,sysid=args.sysid, pythonversion=args.pythonversion))
    os.chmod(os.path.join(rootdir, 'startserver_development.sh'), 0o755)

    if not os.path.exists(os.path.join(rootdir, 'Dockerfile')):
        with open(os.path.join(CLAMDIR, 'config','template.Dockerfile'),'r',encoding='utf-8') as f_in:
            with open(os.path.join(rootdir, 'Dockerfile'),'w',encoding='utf-8') as f_out:
                f_out.write(f_in.read().replace("{sys_id}", args.sysid))
    else:
        print("WARNING: Dockerfile already seems to exists, defiantly refusing to overwrite",file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(os.path.join(sourcedir, args.sysid + '.config.yml')):
        with open(os.path.join(CLAMDIR, 'config','template.config.yml'),'r',encoding='utf-8') as f_in:
            with open(os.path.join(sourcedir, args.sysid + '.config.yml'),'w',encoding='utf-8') as f_out:
                f_out.write(f_in.read().replace("{sys_id}", args.sysid))
    else:
        print("WARNING: YAML configuration file already seems to exists, defiantly refusing to overwrite",file=sys.stderr)
        sys.exit(2)


    with open(os.path.join(rootdir, 'startserver_production.sh'),'w',encoding='utf-8') as f:
        f.write("""#!/bin/sh
set -e
docker build -t "{sysid}" .

#Note, this datadir will be non-persistent, you will likely want to change this in production settings
DATADIR=$(mktemp -d)
chmod go+wx "$DATADIR" #allow subuids/subgids to make directories, needed to prevent permission denied errors
HOST_PORT={port}

#At this point you can pass any environment variables you use in your {sysid}.config.yml, pass them via --env
docker run --rm --volume "$DATADIR:/data" -p "$HOST_PORT:80" --env CLAM_ROOT=/data/{sysid}-userdata --env CLAM_USE_FORWARDED_HOST=0 "{sysid}"

# In many production scenarios, you will not invoke this script manually but instead use a kubernetes deployment (setting the necessary env variables) or a docker-compose.yml
# It is strongly recommended to deploy the container behind a reverse proxy that handles SSL, make sure to pass CLAM_USER_FORWARDED_HOST=1 when running the container in that case.

echo "Navigate to http://localhost:{port} to access the deployed webservice"
""".format(sysid=args.sysid,port=args.port))

    os.chmod(os.path.join(rootdir , 'startserver_production.sh'), 0o755)

    with open(os.path.join(rootdir, '.gitignore'),'w',encoding='utf-8') as f:
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

    with open(os.path.join(rootdir, '.dockerignore'),'w',encoding='utf-8') as f:
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

To develop your webservice, you need to edit the following files:

* ``{sourcedir}/{sysid}.py`` - This is your service configuration file, here you define what goes in and out of the webservice.
* ``{sourcedir}/{sysid}.config.yml`` - This external configuration contains deployment configuration options. It is only used if no host-specific yaml file ({sysid}.$hostname.yml) can be found.
* ``{sourcedir}/{sysid}_wrapper.py`` - This is your system wrapper script (Python) where you implement the logic to call the tool that underlies your webservice
* ``{sourcedir}/{sysid}_wrapper.sh`` - If you prefer to use a simple shell script instead of Python, than use this instead of the above one, other languages are possible too but we have no templates for those.
* ``{sourcedir}/setup.py`` - Set setup.py for your CLAM project, allows you to ship it as a Python package and publish it in the Python Package Index. Adapt the software metadata and when needed the dependencies.
* ``{sourcedir}/Dockerfile`` - The Dockerfile for your project, allows you to build a self-contained container. Recommended for deployment on production servers. Adapt the software metadata and when needed the dependencies.

It is strongly recommended to keep host/deployment specific settings out of the main service configuration file and instead put it in
external configuration files. You can make static external configuration files per hostname (config.$HOSTNAME.yml)
or you can use the provided `{sysid}.config.yml` and use environment variables to set the values at run-time. This is the preferred set-up in combination with Docker.

Create a new one
for each host you plan to deploy this webservice on.

Consult the CLAM Documentation and/or instruction videos on
https://proycon.github.io/clam for further details.

Also don't forget to edit the metadata in the setup script ``{rootdir}/setup.py`` and run ``python setup.py install`` to install the webservice after you made any changes (the start scripts provided will do so automatically for you). This ``setup.py`` also enables you to publish your webservice to the Python Package Index.
""".format(sourcedir=sourcedir,rootdir=rootdir,sysid=args.sysid)


    print(s,file=sys.stderr)

    s2 = """
START YOUR WEBSERVICE
-------------------------

Whilst you are in the process of building your CLAM webservice, you can start
and test your webservice using the built-in development webserver, start it
with ``./startserver_development.sh`` . This takes care of any installation as well.
Once started, you can point your browser to the URL advertised by this script.

DEPLOYING YOUR WEBSERVICE IN PRODUCTION (for system administrators)
----------------------------------------------------------------------

For production use, we recommend using Docker/OCI containers. A Dockerfile has been generated for your project. It is based on Alpine Linux and 
uses nginx and uwsgi to serve the webservice. A ``./startserver_production.sh`` script has been provided to build and launch the container. 

If you do not want to use the container, the Dockerfile still provides valuable insight into how to set up a CLAM webservice. Alternatively, the CLAM Documentation at 
https://clam.readthedocs.io/en/latest/deployment.html explains how to deploy in other settings (e.g. using Apache instead of nginx).

VERSION CONTROL
-----------------

We *strongly* recommend you to put your project under version control (e.g. git).
To create a new git repository::

    cd {rootdir}
    git init
    git add *
    git commit -m "generated by clamnewproject"

VIRTUAL ENVIRONMENT
--------------------

We strongly recommend the use of a Python virtual environment for your CLAM webservice during development.
""".format(rootdir=rootdir,sysid=args.sysid)

    print( s2,file=sys.stderr)

    print( "\n(All of this information can be read again in the INSTRUCTIONS.rst file)",file=sys.stderr)
    print( f"(Your project can be found in {rootdir})",file=sys.stderr)

    with open(os.path.join(rootdir, "INSTRUCTIONS.rst"),'w',encoding='utf-8') as f:
        f.write(s + s2)

    with open(os.path.join(rootdir,"INSTALL"),'w',encoding='utf-8') as f:
        f.write("""Install this webservice and all python dependencies (including CLAM itself) as follows:

 $ pip install .

You may need to use sudo for global installation. We recommend the use of a Python virtual environment.

We recommmend using Docker/OCI containers for production deployments, build and run one using:

 $ ./startserver_production.sh 

Check the contents of that script for further explanations.

""".format(sysid=args.sysid))


if __name__ == "__main__":
    main()
