import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hello_map.settings')

# Gunicorn uses this entry point to run Django.
application = get_wsgi_application()
