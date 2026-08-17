"""ASGI entry point.

Present so the project can adopt Django Channels later without restructuring;
nothing async is served today.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
