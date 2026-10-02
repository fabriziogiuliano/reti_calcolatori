# A tiny web server that answers (almost) only with redirects.
# Run: python redirect_server.py    then open http://localhost:8000/a
from http.server import BaseHTTPRequestHandler, HTTPServer

# path -> (status code, where to go next)
ROUTES = {
    '/a':     (301, '/b'),                     # permanent redirect
    '/b':     (302, '/c'),                     # temporary redirect
    '/loop':  (302, '/loop'),                  # redirects to itself forever
    '/unipa': (302, 'https://www.unipa.it/'),  # redirect to another host
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ROUTES:
            code, location = ROUTES[self.path]
            self.send_response(code)                # status line
            self.send_header('Location', location)  # where to go next
            self.end_headers()                      # empty line: end of headers
        elif self.path == '/c':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>You made it!</h1>')  # body
        else:
            self.send_error(404)

print('Listening on http://localhost:8000 ...')
HTTPServer(('', 8000), Handler).serve_forever()
