from django.contrib import admin
from django.core.exceptions import ValidationError

from django_auth_recovery_codes.forms.schedule_form import RecoveryCodeCleanUpSchedulerForm

from .models import (RecoveryCode, 
                     RecoveryCodeCleanUpScheduler, 
                     RecoveryCodesBatch, 
                     RecoveryCodeAudit, 
                     RecoveryCodePurgeHistory,
                     RecoveryCodeAuditScheduler,
                     RecoveryCodeEmailLog,
                     )



class RecoveryCodeEmailLogAdmin(admin.ModelAdmin):
    list_display = ["id", "from_email", "to_email", "subject", "status", "created_on"]


class RecoveryCodePurgeHistoryAdmin(admin.ModelAdmin):
    """"""
    list_display     = ["id", "name", "timestamp", "total_batches_purged", "retention_days"]
    readonly_fields  = ["total_codes_purged", "retention_days", "total_batches_purged"]
   

class RecoveryCodeCleanupSchedulerAdmin(admin.ModelAdmin):
    """"""
    form = RecoveryCodeCleanUpSchedulerForm
    list_display    = ["id", "name", "enable_scheduler", "run_at", "next_run", "retention_days", "log_per_code", "schedule_type"]   
    help_texts = {
            'schedule': 'Choose the frequency for this task (admin-only help text).'
        }
    
    def save_form(self, request, form, change):
        return super().save_form(request, form, change)
   

class RecoveryCodeAuditSchedulerAdmin(admin.ModelAdmin):
    """"""
    form = RecoveryCodeCleanUpSchedulerForm
    list_display  = ["id", "name", "enable_scheduler", "run_at", "next_run", "retention_days", "schedule_type"]   
    help_texts = {
            'schedule': 'Choose the frequency for this task (admin-only help text).'
        }

    def save_form(self, request, form, change):
        return super().save_form(request, form, change)
   
        



class RecoveryCodeAuditAdmin(admin.ModelAdmin):
    list_display          = ["id", "action", "deleted_by", "user_issued_to", "number_deleted", "number_issued", "timestamp", "updated_at"]
    list_display_links    = ["id", "user_issued_to"]
    list_per_page         = 25
    readonly_fields       = ["id", "timestamp"]
    list_filter           = ["action", ]
    search_fields         = ["id", "user__username", "user__email", "action"]
    ordering              = ["-timestamp",]


class RecoveryCodesBatchAdmin(admin.ModelAdmin):
    list_display          = ["id", "user", "number_issued", "status", "number_removed", "created_at", "modified_at"]
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
                             ]
    list_filter           = ["status", "automatic_removal", ]
    search_fields         = ["id", "user__username", "user__email"]
    ordering              = ["-created_at",]
  

    fieldsets = [
        ("Identification", {
            "fields": ("id", "status"),
        }),
        ("Batch details", {
            "fields": ( "automatic_removal",
                        "number_issued", 
                       "number_removed", 
                        "number_used",
                       "requested_attempt",
                      
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

    list_display       = ["id", "status", "is_deactivated", "mark_for_deletion", "automatic_removal", "created_at", "modified_at"]
    list_display_links = ["id"]
    list_per_page      = 25
    readonly_fields    = ["id", "created_at", "modified_at", "hash_code", "days_to_expire", "user", "batch", "is_used", "status"]
    list_filter        = ["automatic_removal", "status"]
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


admin.site.register(RecoveryCodesBatch, RecoveryCodesBatchAdmin)
admin.site.register(RecoveryCode, RecoveryCodeAdmin)
admin.site.register(RecoveryCodeAudit, RecoveryCodeAuditAdmin)
admin.site.register(RecoveryCodeCleanUpScheduler, RecoveryCodeCleanupSchedulerAdmin)
admin.site.register(RecoveryCodePurgeHistory, RecoveryCodePurgeHistoryAdmin)
admin.site.register(RecoveryCodeAuditScheduler, RecoveryCodeAuditSchedulerAdmin)
admin.site.register(RecoveryCodeEmailLog, RecoveryCodeEmailLogAdmin)