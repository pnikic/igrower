# Servers: (server, port)
# Hotmail: (smtp.live.com, 25)
# Gmail: (smtp.gmail.com, 587) - Activation of less secure apps needed (https://myaccount.google.com/lesssecureapps)

import smtplib
import os.path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

def send_mail(send_from, send_to, subject, message, files=[], server="localhost", port=587, username='', password='', use_tls=True):
    """ Compose and send email with provided info and attachments.

    Arguments:
        send_from (str): Sender address
        send_to (list[str]): Recipient address
        subject (str): Message title
        message (str): Message body
        files (list[str]): List of file paths to be attached to email
        server (str): Mail server host name
        port (int): Port number
        username (str): Server auth username
        password (str): Server auth password
        use_tls (bool): use TLS mode """

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(path)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()
