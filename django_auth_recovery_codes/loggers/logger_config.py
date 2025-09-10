# 
# ===========================================================
# Logging Configuration for Django Auth Recovery Codes Project
# ===========================================================

# Purpose:
# --------
# This file sets up all logging for the project, including module-specific logs
# and a global combined log. It ensures developers and maintainers can quickly
# trace events, errors, and workflow steps in separate, readable log files.

# Key Design:
# -----------
# 1. **Dedicated file per module**: Each main component (views helper, email sender,
#    auth recovery codes, etc.) writes to its own log file. This makes debugging
#    easier because you know exactly where to look.

# 2. **Combined 'all_debug.log'**: Every logger also writes to 'all_debug.log'
#    for a full project-wide overview.

# 3. **Propagation Control**: Module-specific loggers have `propagate=False` to
#    prevent duplicate logging in the root logger. Only loggers that explicitly
#    need to bubble should set `propagate=True`.

# 4. **Root logger**: Captures any logs not handled by module-specific loggers,
#    ensuring nothing gets lost.

# Why this setup matters:
# -----------------------
# - Previous setups sometimes “lost” log messages in module-specific files
#   because the logger didn’t have the right handler attached.
# - Using `propagate=True` incorrectly caused duplicate logs in multiple files.
# - This configuration makes it clear which file each log goes to and avoids
#   accidental duplication.

# Usage:
# ------
# - Grab a logger for the module loggers.py file and you good to go`.

# - Example:
#     from .loggers.loggers import view_logger  
#    
#     view_logger.debug("Debug message here")

# - This will automatically write to both the module-specific file and `all_debug.log`.
#
# 
#  
# Usage in Django settings:
# -------------------------
#
# - Export this dict as `DJANGO_AUTH_RECOVERY_CODES_LOGGING`.
# - Merge it with existing LOGGING dict:
#     from .logger.loggers import DJANGO_AUTH_RECOVERY_CODES_LOGGING
#     LOGGING = {**LOGGING, **DJANGO_AUTH_RECOVERY_CODES_LOGGING}

# - If you don't already have a LOGGING dict, simply assign:
#     LOGGING = DJANGO_AUTH_RECOVERY_CODES_LOGGING
# # ===========================================================
# 

from pathlib import Path


# Default log directory inside the project
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)


# Exportable logging dict e.g from .logger.loggers import DJANGO_AUTH_RECOVERY_CODES_LOGGING
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
        # Views helper
        "app.views_helper": {
            "level": "DEBUG",
            "handlers": ["view_helper_file", "all_file"],
            "propagate": False,
        },
        # Email sender
        "email_sender": {
            "level": "DEBUG",
            "handlers": ["email_file", "all_file"],
            "propagate": False,
        },
        "email_sender.purge": {
            "level": "DEBUG",
            "handlers": ["email_purge_file", "all_file"],
            "propagate": False,
        },
        # Auth recovery codes
        "auth_recovery_codes": {
            "level": "DEBUG",
            "handlers": ["auth_codes_file", "all_file"],
            "propagate": False,
        },
        "auth_recovery_codes.purge": {
            "level": "DEBUG",
            "handlers": ["auth_codes_purge_file", "all_file"],
            "propagate": False,
        },
        "auth_recovery_codes.audit": {
            "level": "DEBUG",
            "handlers": ["audit_file", "all_file"],
            "propagate": False,
        },
        # Django Q internals
        "django_q": {
            "level": "DEBUG",
            "handlers": ["django_q_file", "all_file"],
            "propagate": False,
        },
    },
}
