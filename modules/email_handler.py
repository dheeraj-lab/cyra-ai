import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

EMAIL_ACCOUNTS = {
    "primary": {
        "email": os.getenv("GMAIL_ADDRESS"),
        "password": os.getenv("GMAIL_APP_PASSWORD")
    },
    "second": {
        "email": os.getenv("GMAIL_ADDRESS_2"),
        "password": os.getenv("GMAIL_APP_PASSWORD_2")
    }
}

def send_email(to, subject, body, attachment_path=None, from_account="primary"):
    try:
        account = EMAIL_ACCOUNTS.get(from_account, EMAIL_ACCOUNTS["primary"])
        gmail = account["email"]
        password = account["password"]

        msg = MIMEMultipart()
        msg['From'] = gmail
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}'
                )
                msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail, password)
        server.sendmail(gmail, to, msg.as_string())
        server.quit()

        return f"Email sent from {gmail} to {to}!"

    except Exception as e:
        return f"Failed to send email: {str(e)}"