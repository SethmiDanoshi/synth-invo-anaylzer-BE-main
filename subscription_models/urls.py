from django.urls import path
from . import views

urlpatterns = [
    path('create_subscription/', views.create_subscription_model, name='create_subscription'),
    path('archive_product/', views.archive_product, name='archive_product'),
    path('get_subscription_models/', views.get_subscription_models, name='get_subscription_models'),
    path('update-subscription-model/', views.update_subscription_model, name='update-price'),
    path('create-feature/', views.create_feature, name='create-feature'),
    path('modify-feature/<uuid:pk>/', views.modify_feature, name='modify-feature'),
    path('remove-feature/<uuid:pk>/', views.remove_feature, name='remove-feature'),
    path('get-features/<uuid:model_id>/', views.get_features, name='get_features'),
]
