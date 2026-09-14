# apps/notifications/routing.py
from django.urls import re_path
from .consumers import AmbulanceDriverConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/ambulance/driver/(?P<ambulance_id>[0-9a-f-]{36})/$',
        AmbulanceDriverConsumer.as_asgi()
    ),
]