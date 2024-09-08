from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/admin/(?P<admin_id>[^/]+)/supplier/(?P<supplier_id>[^/]+)/$', consumers.AdminSupplierChatConsumer.as_asgi()),
    re_path(r'ws/chat/admin/(?P<admin_id>[^/]+)/organization/(?P<organization_id>[^/]+)/$', consumers.AdminOrganizationChatConsumer.as_asgi()),
]
