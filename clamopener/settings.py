from os import uname

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Maarten van Gompel', 'proycon@anaproy.nl'),
    ('Antal van den Bosch', 'Antal.vdnBosch@uvt.nl'),
    ('Martin Reynaert', 'reynaert@uvt.nl'),
)



MANAGERS = ADMINS

if uname()[1] == 'aurora' or uname()[1] == 'malaga':
    #proycon's laptop/server
    DOMAIN = 'webservices.ticc.uvt.nl'
    BASEURL = 'http://' + DOMAIN + '/'
    ROOTDIR = '/home/proycon/work/clam/clamopener/'    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': '/home/proycon/work/clam/clamopener/db',                  # Or path to database file if using sqlite3.
            'USER': '',                      # Not used with sqlite3.
            'PASSWORD': '',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }
    REALM = 'CLAM-TICC'
    MASTER_PASSWORD = 'a965704891a834de6e704fccb2f9a95c'  #hashlib.md5('secret').hexdigest()
    FROMMAIL = 'proycon@anaproy.nl'
    
    SERVICES = [
        {
            'url': 'http://'  + DOMAIN + '/ucto/',
            'name': 'Ucto Tokeniser',
            'description': "Ucto is a unicode-compliant tokeniser. It takes input in the form of one or more untokenised texts, and subsequently tokenises them. Several languages are supported, but the software is extensible to other languages."
        },    
    ]
else:
    #assuming ILK server
    DOMAIN = 'webservices.ticc.uvt.nl'
    BASEURL = 'http://' + DOMAIN + '/'
    ROOTDIR = '/var/www/clam/clamopener/'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'clamopener',             # Or path to database file if using sqlite3.
            'USER': 'clamopener',            # Not used with sqlite3.
            'PASSWORD': '',                  # Not used with sqlite3.
            'HOST': 'stheno.uvt.nl',         # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }
    REALM = 'CLAM-TICC'
    MASTER_PASSWORD = 'a965704891a834de6e704fccb2f9a95c'  #hashlib.md5('secret').hexdigest()
    FROMMAIL = 'automailer@webservices.ticc.uvt.nl'
    
    SERVICES = [
        {
            'url': 'http://'  + DOMAIN + '/ucto/',
            'name': 'Ucto Tokeniser',
            'description': "Ucto is a unicode-compliant tokeniser. It takes input in the form of one or more untokenised texts, and subsequently tokenises them. Several languages are supported, but the software is extensible to other languages."
            'website': 'http://ilk.uvt.nl/ucto/',
        },    
        {
            'url': 'http://'  + DOMAIN + '/frog/',
            'name': 'Frog',
            'description': "Frog is a suite containing a tokeniser, PoS-tagger, lemmatiser, morphological analyser, and dependency parser for Dutch, developed at Tilburg University. It is the successor of Tadpole."
            'website': 'http://ilk.uvt.nl/frog/',
        },      
        {
            'url': 'http://'  + DOMAIN + '/valkuil/',
            'name': 'Valkuil',
            'description': "Valkuil is a Dutch spelling-corrector system."
            'website': 'http://valkuil.net',
        },     
        {
            'url': 'http://'  + DOMAIN + '/oersetter/',
            'name': 'Oersetter',
            'description': "Oersetter is a Frisian-Dutch, Dutch-Frisian Machine Translation system"
            'website': 'http://oersetter.nl',
        },     
    ]
    
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ROOTDIR + 'style/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/style/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'vi+223a(t0eu-f2oyp&$2)#swjx9_y9dlbkdkye%+2c3#@7&a6'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'clamopener.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ROOTDIR + 'templates',
)

INSTALLED_APPS = (
    #'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    #'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'clamopener.clamindex',
    'clamopener.clamusers',
)
