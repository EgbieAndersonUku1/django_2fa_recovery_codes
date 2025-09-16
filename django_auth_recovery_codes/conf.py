FLAG_VALIDATORS = {
    
    # --- Cache Settings ---
    "DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL must be an integer.",
        "error_id": "django_auth_recovery_codes.E001",
        "warning_id": "django_auth_recovery_codes.W001",
    },
    "DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN must be an integer.",
        "error_id": "django_auth_recovery_codes.E002",
        "warning_id": "django_auth_recovery_codes.W002",
    },
    "DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX must be an integer.",
        "error_id": "django_auth_recovery_codes.E003",
        "warning_id": "django_auth_recovery_codes.W003",
    },

    # --- Cooldown Settings ---
    "DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN must be an integer.",
        "error_id": "django_auth_recovery_codes.E004",
        "warning_id": "django_auth_recovery_codes.W004",
    },
    "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER must be an integer.",
        "error_id": "django_auth_recovery_codes.E005",
        "warning_id": "django_auth_recovery_codes.W005",
    },
    "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT must be an integer.",
        "error_id": "django_auth_recovery_codes.E006",
        "warning_id": "django_auth_recovery_codes.W006",
    },

    # --- Admin / Email Settings ---
    "DJANGO_AUTH_RECOVERY_CODES_ADMIN_SENDER_EMAIL": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_ADMIN_SENDER_EMAIL is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_ADMIN_SENDER_EMAIL must be a string.",
        "error_id": "django_auth_recovery_codes.E007",
        "warning_id": "django_auth_recovery_codes.W007",
    },

    # --- Format Settings ---
    "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT must be a string.",
        "error_id": "django_auth_recovery_codes.E008",
        "warning_id": "django_auth_recovery_codes.W008",
    },

    # --- File / Key Settings ---
    "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME must be a string.",
        "error_id": "django_auth_recovery_codes.E009",
        "warning_id": "django_auth_recovery_codes.W009",
    },
    
    "DJANGO_AUTH_RECOVERY_KEY": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_KEY is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_KEY must be a string.",
        "error_id": "django_auth_recovery_codes.E010",
        "warning_id": "django_auth_recovery_codes.W010",
    },

    # --- Audit / Retention Settings ---
    "DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS must be an integer.",
        "error_id": "django_auth_recovery_codes.E011",
        "warning_id": "django_auth_recovery_codes.W011",
    },
    "DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP": {
        "type": bool,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP must be a boolean.",
        "error_id": "django_auth_recovery_codes.E012",
        "warning_id": "django_auth_recovery_codes.W012",
    },
    "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS": {
        "type": int,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS must be an integer.",
        "error_id": "django_auth_recovery_codes.E013",
        "warning_id": "django_auth_recovery_codes.W013",
    },

    # --- Admin Email Settings ---
    "DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER must be a string.",
        "error_id": "django_auth_recovery_codes.E014",
        "warning_id": "django_auth_recovery_codes.W014",
    },
    "DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL must be a string.",
        "error_id": "django_auth_recovery_codes.E015",
        "warning_id": "django_auth_recovery_codes.W015",
    },
    "DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME": {
        "type": str,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME must be a string.",
        "error_id": "django_auth_recovery_codes.E016",
        "warning_id": "django_auth_recovery_codes.W016",
    },

    # --- Logger / Email Log Settings ---
    "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER": {
        "type": bool,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER must be a boolean.",
        "error_id": "django_auth_recovery_codes.E017",
        "warning_id": "django_auth_recovery_codes.W017",
    },
    "DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG": {
        "type": bool,
        "warning_if_missing": "DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG is not set in settings.py.",
        "error_if_wrong_type": "DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG must be a boolean.",
        "error_id": "django_auth_recovery_codes.E018",
        "warning_id": "django_auth_recovery_codes.W018",
    },

   
}
