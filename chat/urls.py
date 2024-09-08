from django.urls import path, re_path
from . import views

urlpatterns = [
    path('history/<uuid:admin_id>/<uuid:user_id>/<str:user_type>/', views.chat_history, name='chat_history'),
    path('users/<uuid:admin_id>/', views.user_list, name='user_list'),
    path('current-user/<uuid:user_id>/', views.current_user, name='current_user'),
    path('admin-list/', views.admin_list, name='admin-list'),
]
