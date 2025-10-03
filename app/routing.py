from django.urls import re_path
from app.consumers import SerialConsumer
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/comport/$', SerialConsumer.as_asgi()),
    re_path(r'ws/measurement/$', SerialConsumer.as_asgi()),
    re_path(r'ws/index/$', consumers.SerialConsumer.as_asgi()),
 
]