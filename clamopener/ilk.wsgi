import os, sys
sys.path.append('/var/www/clam/clamopener/')
sys.path.append('/var/www/clam/')
os.environ['PYTHONPATH'] = '/var/www/clam/'

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
