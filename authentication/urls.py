# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('organization/signup/', views.organization_signup, name='signup'),
    path('organization/signin/', views.organization_signin, name='signin'),
    path('supplier/add/', views.add_supplier, name='add-supplier'),
    path('supplier/signin/', views.supplier_signin, name='sup-signin'),
    path('admin/signup/', views.admin_signup, name='adm-signup'),
    path('admin/signin/', views.admin_signin, name='adm-signin'),
    path('organization/protected/', views.organization_protected_view, name='protected_org'),
    path('supplier/protected/', views.supplier_protected_view, name='sup_org'),
    path('admin/protected/', views.admin_protected_view, name='adm_org'),
    path('otp/verify-otp/', views.verify_otp_view, name='verify-otp'), 
    path('otp/resend-otp/', views.resend_otp_view, name= 'resend-otp'),
    path('supplier/check/', views.check_supplier_exists, name= 'check-supplier-exists'),
    path('supplier/pending-requests/', views.pending_requests_supplier_view, name= 'pending_requests_supplier_view'),
    path('organization/pending-requests/', views.pending_requests_organization_view, name= 'pending_requests_org_view'),
    path('accept-request/', views.add_supplier_to_organization, name='add-supplier to org'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('change-password/', views.change_password, name='change-password'),
    path('get-org-by-sup/', views.get_org_by_supplier, name='get-org-by-sup'),
    path('organization/profile/<uuid:organization_id>/', views.organization_profile, name='organization-profile'),

]


