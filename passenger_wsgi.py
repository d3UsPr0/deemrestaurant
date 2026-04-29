import os
import sys

# Add your project path
sys.path.insert(0, os.path.dirname(__file__))

os.environ['DJANGO_SETTINGS_MODULE'] = 'deemrestaurant.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()