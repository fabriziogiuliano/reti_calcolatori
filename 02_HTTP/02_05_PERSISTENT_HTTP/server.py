# A web server with an emulated RTT.
# It logs every TCP connection (open / close) and every request on it.
import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

RTT = 0.5                              # seconds: our (artificial) round-trip time

logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d  %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('server')

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'      # the server can do both: the CLIENT decides (curl --http1.0 / --http1.1)

    def handle(self):                  # called once per TCP connection
        port = self.client_address[1]
        log.info('[port %d] connection OPEN', port)
        time.sleep(RTT)                # the TCP handshake costs 1 RTT
        self.requests = 0
        super().handle()               # serves all the requests of this connection
        log.info('[port %d] connection CLOSED after %d request(s)', port, self.requests)

    def do_GET(self):                  # called once per request
        time.sleep(RTT)                # request + response cost 1 RTT
        self.requests += 1
        log.info('[port %d]   %s %s %s', self.client_address[1], self.command, self.path, self.request_version)
        body = f'You asked for {self.path}\n'.encode()
        self.send_response(200)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):      # hide the default log: we use our own
        pass

log.info('Server on http://localhost:8000 (%s, RTT %s s)', Handler.protocol_version, RTT)
HTTPServer(('', 8000), Handler).serve_forever()
