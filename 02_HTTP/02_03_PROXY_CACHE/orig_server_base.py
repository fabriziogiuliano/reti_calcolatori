# NOT used in the README steps: the first version of origin_server.py, kept for comparison.
# The delay is in do_GET, before the answer is chosen: EVERY answer (200, 304, 404) takes 2 s.
# The current origin_server.py puts the delay in copyfile(): only answers with a file wait.

# The ORIGIN server: the real web site, far away from the clients.
# It serves the files in www/, but every answer takes 2 seconds (long distance, slow link).
import os
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer

DELAY = 2   # seconds
WWW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www')

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        time.sleep(DELAY)    # emulate a far-away server
        super().do_GET()     # send the file from www/

print(f'Origin server on http://localhost:8000 (delay {DELAY} s) ...')
HTTPServer(('', 8000), partial(Handler, directory=WWW)).serve_forever()
