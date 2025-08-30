from django.contrib import admin

from .models import RecoveryCode, RecoveryCodeCleanUpScheduler, RecoveryCodesBatch, RecoveryCodeAudit





class RecoveryCodeAuditAdmin(admin.ModelAdmin):
    list_display          = ["id", "action", "deleted_by", "user", "deleted_by", "batch", "timestamped"]
    list_display_links    = ["id", "user"]
    list_per_page         = 25
    readonly_fields       = ["id", "timestamped", "modified_at"]
    list_filter           = ["action", ]
    search_fields         = ["id", "user__username", "user__email", "action"]
    ordering              = ["-timestamped",]


class RecoveryCodesBatchAdmin(admin.ModelAdmin):
    list_display          = ["id", "user", "number_issued", "status", "number_removed", "created_at", "modified_at"]
    list_display_links    = ["id", "user"]
    list_per_page         = 25
    readonly_fields       = ["id", "created_at", "modified_at"]
    list_filter           = ["status", "automatic_removal", ]
    search_fields         = ["id", "user__username", "user__email"]
    ordering              = ["-created_at",]

    fieldsets = [
        ("Identification", {
            "fields": ("id", "status"),
        }),
        ("Batch details", {
            "fields": ("number_issued", 
                       "number_removed", 
                       "automatic_removal",
                         "expiry_date", "viewed", "downloaded", "emailed", "generated"),
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
    readonly_fields    = ["id", "created_at", "modified_at", "hash_code", "days_to_expire"]
    list_filter        = ["automatic_removal", "status"]
    search_fields      = ["id", "status", "user__email", "user__username"]
    exclude            = ("look_up_hash", )

    fieldsets = [
        ("Identification", {
            "fields": ("id", "hash_code", "is_deactivated", "is_used", "mark_for_deletion", "status", "days_to_expire"),
        }),
        ("Batch details", {
            "fields": ("batch", ),
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