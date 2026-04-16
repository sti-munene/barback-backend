"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")

load_dotenv(dotenv_path)
from django.core.wsgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", str(os.getenv("SETTINGS_MODULE")))

application = get_asgi_application()
