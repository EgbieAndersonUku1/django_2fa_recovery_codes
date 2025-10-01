from django.contrib import admin
from django_auth_recovery_codes.forms.schedule_form import RecoveryCodeCleanUpSchedulerForm

from .models import (RecoveryCode, 
                     RecoveryCodeCleanUpScheduler, 
                     RecoveryCodesBatch, 
                     RecoveryCodeAudit, 
                     RecoveryCodePurgeHistory,
                     RecoveryCodeAuditScheduler,
                     RecoveryCodeNotification,
                     RecoveryCodeEmailLog,
                     RecoveryCodeSetup,
                     LoginRateLimiter,
                     LoginRateLimterAudit,
                     )



class LoginRateLimiterAdmin(admin.ModelAdmin):
    list_display    = ["id", "user", "login_attempts", "max_login_attempts", "last_attempt", "created_at", "modified_at"]
    readonly_fields = ["id", "user", "login_attempts", "max_login_attempts", "last_attempt", "created_at", "modified_at"]



"""
    user           = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    modified_at    = models.DateTimeField(auto_now=True)
    login_attempts = models.PositiveSmallIntegerField(default=0)


"""

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 25


class LoginRateLimterAuditAdmin(BaseAdmin):
    """Display the fields for the LoginRateLimit model inside the admin interface"""
    
    list_display         = ["id", "user",  "login_attempts", "created_at", "modified_at"]
    readonly_fields      = ["id", "user",  "login_attempts", "created_at", "modified_at"]
    search_fields        = ["id", "user", "user__email", "user__username"]
    list_display_links   = ["id", "user"]


class RecoveryCodeSetupAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodeSetup model.

    Displays recovery code setup records in the admin interface with 
    the associated user, verification timestamp, and success status.
    """
    list_display    = ["id", "user", "verified_at", "success"]
    readonly_fields = ["id", "user", "verified_at", "success"]
    search_fields   = ["id", "user", "success"]



class RecoveryCodeEmailLogAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodeEmailLog model.

    Displays email log entries for recovery codes in the admin interface,
    including sender and recipient details, subject, delivery status, 
    creation timestamp, and full email body (read-only).
    """
    list_display         = ["id", "from_email", "to_email", "subject", "status", "created_on"]
    readonly_fields      = ["id", "from_email", "to_email", "subject", "status", "created_on", "email_body"]
    list_display_links   = ["id", "from_email", "to_email"]
    search_fields        = ["from_email", "to_email", "subject"]



class RecoveryCodePurgeHistoryAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodePurgeHistory model.

    Displays purge history records for recovery codes in the admin interface,
    including the purge name, execution timestamp, number of batches purged,
    and retention period in days.
    """
    list_display       = ["id", "name", "timestamp", "total_batches_purged", "retention_days"]
    readonly_fields    = ["total_codes_purged", "retention_days", "total_batches_purged"]
    search_fields      = ["id", "name"]
    list_display_links = ["id", "name"]
    list_filter        = ["timestamp", "retention_days"]



class RecoveryCodeCleanupSchedulerAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodeCleanupScheduler model.

    Allows management of recovery code cleanup schedulers in the admin interface,
    including enabling/disabling the scheduler, setting run times, retention period,
    schedule type, and displaying status and bulk delete options (read-only).
    """

    form = RecoveryCodeCleanUpSchedulerForm
    list_display    = ["id", "name", "enable_scheduler", "run_at", "next_run", "retention_days", "schedule_type"]   
    help_texts      = {
            'schedule': 'Choose the frequency for this task (admin-only help text).'
        }
    readonly_fields    = ["status", "bulk_delete"]
    list_display_links = ["id", "name"]

    def save_form(self, request, form, change):
        return super().save_form(request, form, change)
   

class RecoveryCodeAuditSchedulerAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodeAuditScheduler model.

    Allows management of audit schedulers for recovery codes in the admin interface,
    including enabling/disabling the scheduler, setting run times, retention period,
    schedule type, and linking to the cleanup form.
    """
    form               = RecoveryCodeCleanUpSchedulerForm
    list_display       = ["id", "name", "enable_scheduler", "run_at", "next_run", "retention_days", "schedule_type"]   
    list_display_links = ["id", "name"]
    help_texts    = {
            'schedule': 'Choose the frequency for this task (admin-only help text).'
        }

    def save_form(self, request, form, change):
        return super().save_form(request, form, change)
   
    

class RecoveryCodeAuditAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodeAudit model.

    Displays audit records for recovery code actions in the admin interface,
    including the type of action, who deleted the codes, the user issued to,
    number of codes deleted or issued, and timestamps for creation and updates.
    """
    list_display          = ["id", "action", "deleted_by", "user_issued_to", "number_deleted", "number_issued", "timestamp", "updated_at"]
    list_display_links    = ["id", "user_issued_to"]
    readonly_fields       = ["id", "action", "deleted_by", "user_issued_to", "number_deleted", "number_issued", "timestamp", "updated_at"]
    list_filter           = ["action", ]
    search_fields         = ["id", "user__username", "user__email", "action"]
    ordering              = ["-timestamp",]




class RecoveryCodesBatchAdmin(BaseAdmin):
    """
    Admin configuration for the RecoveryCodesBatch model.

    Displays batches of recovery codes in the admin interface, including the 
    associated user, batch status, number of codes issued, used, or removed, 
    timestamps, expiry, and other metadata. Supports filtering, searching, 
    and detailed fieldsets for better organisation of batch information.
    """
    list_display          = ["id", "user", "number_issued", "last_attempt", "status", "number_removed", "created_at", "modified_at"]
    list_display_links    = ["id", "user"]
    list_per_page         = 25
    readonly_fields       = ["id", "created_at", "modified_at", "number_removed", 
                             "number_used", "requested_attempt", "number_issued",
                             "expiry_date",
                             "viewed",
                             "downloaded",
                             "emailed",
                             "generated",
                             "user",
                             "deleted_at",
                             "deleted_by",
                             "status",
                             "last_attempt",
                             ]
    list_filter           = ["status", "automatic_removal", ]
    search_fields         = ["id", "user__username", "user__email"]
    ordering              = ["-created_at",]
    fieldsets             = [
            ("Identification", {
                "fields": ("id", "status"),
            }),
        ("Batch details", {
            "fields": ( "automatic_removal",
                        "number_issued", 
                        "number_removed", 
                        "number_used",
                        "requested_attempt",
                        "last_attempt",
                      
                         "expiry_date", "viewed", "downloaded", "emailed", "generated",
                          "cooldown_seconds",
                    
                       "multiplier",
                         ),
        }),
        ("User associations", {
            "fields": ("user",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "modified_at"),
        }),
        ("Deletion", {
            "classes": ("collapse",), 
            "fields": ("deleted_at", "deleted_by"),
        }),
    ]


class RecoveryCodeAdmin(admin.ModelAdmin):
    """
    Admin configuration for the RecoveryCode model.

    Displays individual recovery codes in the admin interface, including their 
    status, usage, deactivation state, deletion flags, automatic removal, 
    creation timestamp, and associated user and batch information.
    """
    list_display       = ["id", "status", "is_used", "is_deactivated", "mark_for_deletion", "automatic_removal", "created_at"]
    list_display_links = ["id"]
    list_per_page      = 25
    readonly_fields    = ["id", "created_at", "modified_at", "hash_code", "days_to_expire", "user", "batch", "is_used", "status"]
    list_filter        = ["automatic_removal", "status", "is_used", "is_deactivated", ]
    search_fields      = ["id", "status", "user__email", "user__username"]
    exclude            = ("look_up_hash", )

    fieldsets = [
        ("Identification", {
            "fields": ("id", "hash_code", "is_deactivated", "is_used", "mark_for_deletion", "status", "days_to_expire"),
        }),
        ("Batch details", {
            "fields": ("batch", "automatic_removal" ),
        }),
        ("User associations", {
            "fields": ("user",),
        }),
        ("Timestamps", {
             "classes": ("collapse",), 
            "fields": ("created_at", "modified_at"),
        }),
       
    ]



class RecoveryNotificationAdmin(BaseAdmin):
    """Tracks the notification"""
    list_display       = ["id", "sent_at", "is_read", "created_at", "modified_at"]
    list_display_links = ["id"]
    readonly_fields    = ["id", "sent_at", "is_read", "created_at", "modified_at"]


admin.site.register(RecoveryCodesBatch, RecoveryCodesBatchAdmin)
admin.site.register(RecoveryCode, RecoveryCodeAdmin)
admin.site.register(RecoveryCodeAudit, RecoveryCodeAuditAdmin)
admin.site.register(RecoveryCodeCleanUpScheduler, RecoveryCodeCleanupSchedulerAdmin)
admin.site.register(RecoveryCodePurgeHistory, RecoveryCodePurgeHistoryAdmin)
admin.site.register(RecoveryCodeAuditScheduler, RecoveryCodeAuditSchedulerAdmin)
admin.site.register(RecoveryCodeEmailLog, RecoveryCodeEmailLogAdmin)
admin.site.register(RecoveryCodeSetup, RecoveryCodeSetupAdmin)
admin.site.register(LoginRateLimiter, LoginRateLimiterAdmin)
admin.site.register(LoginRateLimterAudit, LoginRateLimterAuditAdmin)
admin.site.register(RecoveryCodeNotification, RecoveryNotificationAdmin)