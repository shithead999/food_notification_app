import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
from users.routing import application as user_ws_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "food_notification.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": user_ws_application,
    }
)
