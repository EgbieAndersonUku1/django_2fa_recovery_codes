from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import LoggerType



def send_recovery_codes_email(sender_email, user, codes, subject= "Your account recovery codes"):
 ( 
    EmailSenderLogger.create() 
        .add_email_sender_instance(EmailSender.create()) 
        .from_address(sender_email) 
        .to(user.username) 
        .with_context({"codes": codes, "username": user.username}) 
        .with_subject(subject) 
        .with_html_template("test_email.html", "django_auth_recovery_codes_email") 
        .with_text_template("test_email.txt", "django_auth_recovery_codes_email") 
        .send()
    )
