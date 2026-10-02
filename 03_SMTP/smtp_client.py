# A mail client (user agent) in Python: it sends one mail to our local server.
# set_debuglevel(1) prints every SMTP command sent and every reply received.
import smtplib

message = """From: Alice <alice@unipa.it>
To: Bob <bob@example.com>
Subject: Hello from Python

Hi Bob,
this mail was sent by smtplib.
"""

with smtplib.SMTP('127.0.0.1', 2525, local_hostname='my-pc') as server:
    server.set_debuglevel(1)                                   # show the conversation
    server.sendmail('alice@unipa.it', ['bob@example.com'], message)   # MAIL FROM, RCPT TO, DATA
