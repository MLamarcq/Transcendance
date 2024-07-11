"""
ASGI config for mysite project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
import logging
logger = logging.getLogger('pong')

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, re_path
from pong import consumers

django_asgi_app = get_asgi_application()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

logger.info(" _@@@@@@_ ")
application = ProtocolTypeRouter({
	"https": django_asgi_app,
	'websocket': URLRouter([
		re_path(r'ws/pong/$', consumers.PongConsumer.as_asgi())
		# path('ws/pong/', consumers.PongConsumer.as_asgi()),
	]),
})

logger.debug("%s", application)