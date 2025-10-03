import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from app.routing import websocket_urlpatterns  # Import your websocket routes

# Explicitly set the environment variable for settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mini_soft.settings')

# Ensure Django is set up properly
django.setup()

# Define application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP protocol
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # Websocket routing
        )
    ),
})
