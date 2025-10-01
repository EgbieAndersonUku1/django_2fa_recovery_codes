import logging

# ----------------------------------------
# default helper
# ----------------------------------------
default_logger  = logging.getLogger(__name__)



# ----------------------------------------
# Attempt guard helper
# ----------------------------------------
attempt_guard_logger  = logging.getLogger("attempt_guard")



# ----------------------------------------
# Views helper
# ----------------------------------------
view_logger          = logging.getLogger("app.views_helper")



# ----------------------------------------
# Email sender
# ----------------------------------------
email_logger       = logging.getLogger("email_sender")
purge_email_logger = logging.getLogger("email_sender.purge")



# ----------------------------------------
# Auth recovery codes
# ----------------------------------------
auth_logger       = logging.getLogger("auth_recovery_codes")
purge_code_logger = logging.getLogger("auth_recovery_codes.purge")
audit_logger      = logging.getLogger("auth_recovery_codes.audit")



# ----------------------------------------
# Django Q internals (optional)
# ----------------------------------------
django_q_logger = logging.getLogger("django_q")
