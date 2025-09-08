from pathlib import Path

# Default log directory inside the project
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)



# Exportable logging dict
DJANGO_AUTH_RECOVERY_CODES_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "all_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "all_debug.log",
            "formatter": "default",
        },
        "view_helper_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "view_helper.log",
            "formatter": "default",
        },
        "email_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "email_sender.log",
            "formatter": "default",
        },
        "email_purge_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "email_purge.log",
            "formatter": "default",
        },
        "auth_codes_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "auth_recovery_codes.log",
            "formatter": "default",
        },
        "auth_codes_purge_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "auth_codes_purge.log",
            "formatter": "default",
        },
        "audit_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "audits.log",
            "formatter": "default",
        },
        "django_q_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "django_q.log",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["all_file"],
        "level": "DEBUG",
    },
    "loggers": {
        "django_q": {
            "level": "DEBUG",
            "handlers": ["django_q_file", "all_file"],
            "propagate": True,
        },
        "app.views_helper": {
            "level": "DEBUG",
            "handlers": ["all_file"],
            "propagate": True,
        },
        "email_sender": {
            "level": "DEBUG",
            "handlers": ["email_file", "all_file"],
            "propagate": True,
        },
        "email_sender.purge": {
            "level": "DEBUG",
            "handlers": ["email_purge_file", "all_file"],
            "propagate": True,
        },
        "auth_recovery_codes": {
            "level": "DEBUG",
            "handlers": ["auth_codes_file", "all_file"],
            "propagate": True,
        },
        "auth_recovery_codes.purge": {
            "level": "DEBUG",
            "handlers": ["auth_codes_purge_file", "all_file"],
            "propagate": True,
        },
        "auth_recovery_codes.audit": {
            "level": "DEBUG",
            "handlers": ["audit_file", "all_file"],
            "propagate": True,
        },
    },
}
