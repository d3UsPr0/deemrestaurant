import sys
import os

# Get the project directory path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deemrestaurant.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()