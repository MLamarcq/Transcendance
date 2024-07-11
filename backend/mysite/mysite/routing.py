from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from . import consumers
from django.urls import re_path

application = ProtocolTypeRouter({
	'websocket': URLRouter([
		re_path(r'ws/pong/(?P<room_name>\w+)/$', consumers.PongConsumer.as_asgi()),
	]),
})

# path('ws/pong/', consumers.PongConsumer.as_asgi()),