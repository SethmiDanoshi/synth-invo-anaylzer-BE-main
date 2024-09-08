from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('invoice-template/', include('invoice_template.urls')),
    path('invoice/', include('invoice.urls')),
    path('subscription-models/', include('subscription_models.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('analysis/', include('invoice_analysis.urls')),
    path('search/', include('search.urls')),
    path('chat/', include('chat.urls')),
   
]


