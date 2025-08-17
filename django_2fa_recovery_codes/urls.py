from django.urls import path
from django_2fa_recovery_codes import views

urlpatterns = [
    path("recovery-codes/", views.recovery_codes_list, name="recovery_codes_list"),
    path("recovery-codes/regenerate/", views.recovery_codes_regenerate, name="recovery_codes_regenerate"),
    path("recovery-codes/verify/", views.recovery_codes_verify, name="recovery_codes_verify"),
    path("2fa/recovery-codes/generate-with-expiry/", views.generate_recovery_code_with_expiry, name="generate_code_with_expiry"),
    path("2fa/recovery-codes/dashboard/", views.recovery_dashboard, name="recovery_dashboard"),

]