# The ORIGIN server: the real web site, far away from the clients.
# It serves the files in www/, but sending a file takes 2 seconds (long distance, slow link).
# An answer without a file (e.g. 304 Not Modified) arrives at once.
import os
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer

DELAY = 2   # seconds
WWW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www')

class Handler(SimpleHTTPRequestHandler):
    # The base do_GET sends status line + headers, then calls copyfile() only if
    # there is a file to send (200). 304 and 404 have no file: no copyfile, no delay.
    # Simplification: fixed delay, not proportional to the file size.
    def copyfile(self, source, outputfile):   # called only when the file is sent
        time.sleep(DELAY)                     # emulate a far-away server
        super().copyfile(source, outputfile)

print(f'Origin server on http://localhost:8000 (delay {DELAY} s) ...')
HTTPServer(('', 8000), partial(Handler, directory=WWW)).serve_forever()
