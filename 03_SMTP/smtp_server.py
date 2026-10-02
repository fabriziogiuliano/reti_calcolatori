# A local mail server (SMTP), port 2525. It does not deliver anything:
# it only prints every mail it receives, split into ENVELOPE and MESSAGE.
import time
from aiosmtpd.controller import Controller

PORT = 2525

class Handler:
    async def handle_DATA(self, server, session, envelope):   # called after the final "."
        print('=' * 60)
        print('ENVELOPE (from the SMTP commands)')
        print('  MAIL FROM:', envelope.mail_from)
        print('  RCPT TO:  ', ', '.join(envelope.rcpt_tos))
        print('MESSAGE (after DATA: headers, empty line, body)')
        print(envelope.content.decode('utf-8', errors='replace'))
        return '250 OK: message accepted'

controller = Controller(Handler(), hostname='127.0.0.1', port=PORT, server_hostname='mail.lab')
controller.start()
print(f'Mail server on 127.0.0.1:{PORT} ...  (Ctrl+c to stop)')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    controller.stop()
