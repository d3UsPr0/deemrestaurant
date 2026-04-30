import os
import sys

# Path to your Django project (folder containing manage.py)
sys.path.insert(0, os.path.dirname(__file__))

# Point to Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deemrestaurant.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()