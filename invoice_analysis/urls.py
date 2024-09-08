from django.urls import path
from . import views

urlpatterns = [
    path('product_price_deviations/', views.product_price_deviations, name='search_invoices'),  
    path('supplier-expenditures/', views.organization_supplier_expenditures, name='supp-expend'),
    path('monthly-expenditure/', views.monthly_expenditures, name='monthly-expenditure'),
    path('suppliers-price-by-month/', views.suppliers_price_by_month, name='suppliers_price_by_month'),
]

