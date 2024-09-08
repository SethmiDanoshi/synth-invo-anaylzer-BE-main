from django.urls import path
from . import views  




urlpatterns = [
   path('save-invoice-template/', views.save_invoice_template, name='save-temaplate'),
   path('update-mapping/', views.update_mapping, name = 'update-mapping'),
   path('get-unmapped-templates/', views.get_unmapped_templates, name = 'get-unmapped-templates'),
   path('get-supplier-template/', views.get_supplier_template, name='get-supplier-template'),
]
