import logging

from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import LoggerType

from django_auth_recovery_codes import notify_user

logger = logging.getLogger("email_sender")

def send_recovery_codes_email(sender_email, user, codes, subject= "Your account recovery codes"):
    email_sender_logger = EmailSenderLogger.create() 
    try:
        ( 
        
            email_sender_logger.create() 
                .add_email_sender_instance(EmailSender.create()) 
                .start_logging_session()
                .config_logger(logger, log_level=LoggerType.INFO)
                .from_address(sender_email) 
                .to(user.username) 
                .with_context({"codes": codes, "username": user.username}) 
                .with_subject(subject) 
                .with_html_template("recovery_codes_email.html", "recovery_codes") 
                .with_text_template("recovery_codes_email.txt", "recovery_codes") 
                .send()
            )
        notify_user(user.id, "Recovery codes email sent successfully!")

    except Exception as e:
        logger.error(f"Failed to send recovery codes: {e}")
        notify_user(user.id, f"Failed to send recovery codes: {e}")

        raise 
