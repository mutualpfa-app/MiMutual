"""
WSGI config for mutual_pfa project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mutual_pfa.settings')

application = get_wsgi_application()