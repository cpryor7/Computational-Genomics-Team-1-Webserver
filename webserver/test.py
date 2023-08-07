from pathlib import Path
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


#with open('jobs/75378079/job_results.zip') as fp:
#    # Create a text/plain message
#    msg = EmailMessage()
#    msg.set_content("Dasdasas")

# me == the sender's email address
# you == the recipient's email address


# Send the message via our own SMTP server.
s = smtplib.SMTP('smtp.gmail.com', 587)
#s.ehlo()
s.starttls()
s.login('team1.webserver@gmail.com', 'wqchfqkllhclmxgo')
email = MIMEMultipart()
#msg.set_content("dsadasdasa")
email['Subject'] = 'TEST'
email['From'] = 'team1.webserver@gmail.com'
email['To'] = "bhavayaggarwal07@gmail.com"

body = "Your results are attached below"
email.attach(MIMEText(body, 'plain'))

part = MIMEBase('application', "octet-stream")
part.set_payload(open('jobs/75378079/job_results.zip', "rb").read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="job_results.zip"')
email.attach(part)
text = email.as_string()
s.sendmail('team1.webserver@gmail.com', 'bhavayaggarwal07@gmail.com', text)

s.quit()