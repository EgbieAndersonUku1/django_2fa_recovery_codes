from django.urls import path
from django_auth_recovery_codes import views

from .sse import sse_notifications

urlpatterns = [
   
    path("auth/recovery-codes/sse/notifications/", sse_notifications, name="recovery_codes_sse"),
    path("auth/recovery-codes/mark-batch-as-deleted/", views.mark_all_recovery_codes_as_pending_delete, name="mark-as-pending"),
    path("auth/recovery-codes/regenerate/", views.recovery_codes_regenerate, name="recovery_codes_regenerate"),
    path("auth/recovery-codes/verify-setup/", views.verify_test_code_setup, name="recovery_codes_verify"),
    path("auth/recovery-codes/delete-codes/", views.delete_recovery_code, name="delete-codes"),
    path("auth/recovery-codes/invalidate-codes/", views.invalidate_user_code, name="invalidate-codes"),
    path("auth/recovery-codes/download-codes/", views.download_code, name="download-codes"),
    path("auth/recovery-codes/email/", views.email_recovery_codes, name="email_recovery_codes"),
    path("auth/recovery-codes/viewed/", views.marked_code_as_viewed, name="marked_code_as_viewed"),
    path("auth/recovery-codes/generate-without-expiry/", views.generate_recovery_code_without_expiry, name="generate_code_without_expiry"),
    path("auth/recovery-codes/generate-with-expiry/", views.generate_recovery_code_with_expiry, name="generate_code_with_expiry"),
    path("auth/recovery-codes/dashboard/", views.recovery_dashboard, name="recovery_dashboard"),
    path("auth/recovery-codes/notifications/", views.fetch_notifications, name="notification"),
    path("auth/recovery-codes/login/", views.login_user, name="login_user"),
    path("auth/recovery-codes/logout/", views.logout_user, name="recovery_codes_logout")

]