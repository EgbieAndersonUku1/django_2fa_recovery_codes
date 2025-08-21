from django.urls import path
from django_auth_recovery_codes import views

urlpatterns = [
    path("auth/recovery-codes/regenerate/", views.recovery_codes_regenerate, name="recovery_codes_regenerate"),
    path("recovery-codes/verify/", views.recovery_codes_verify, name="recovery_codes_verify"),
    path("auth/recovery-codes/email/", views.email_recovery_codes, name="email_recovery_codes"),
    path("auth/recovery-codes/viewed/", views.marked_code_as_viewed, name="marked_code_as_viewed"),
    path("auth/recovery-codes/generate-without-expiry/", views.generate_recovery_code_without_expiry, name="generate_code_without_expiry"),
    path("auth/recovery-codes/generate-with-expiry/", views.generate_recovery_code_with_expiry, name="generate_code_with_expiry"),
    path("auth/recovery-codes/dashboard/", views.recovery_dashboard, name="recovery_dashboard"),

]