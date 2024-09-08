from django.urls import path
from . import views

urlpatterns = [
    path('search-invoices/', views.search_invoices, name='search_invoices'),  
    path('get-prod-by-org/', views.organization_products, name='get-prod-list'), 
    path('build-query/', views.build_query, name='build-query'),  
    path('execute-search/', views.execute_search, name='execute-search'),   
    
]
