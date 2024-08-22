from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from .consumers import NotificationConsumer

application = ProtocolTypeRouter(
    {
        "websocket": URLRouter(
            [
                re_path(r"ws/notification/$", NotificationConsumer.as_asgi()),
            ]
        )
    }
)
