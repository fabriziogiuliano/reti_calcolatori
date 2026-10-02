# A caching PROXY: it sits between the clients and the origin server.
#   HIT  -> the object is in the cache: answer immediately
#   MISS -> ask the origin, keep a copy, then answer
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ORIGIN = 'http://localhost:8000'   # the site we stand in front of (CDN case)
cache = {}                          # url -> (content type, body)
hits = misses = 0

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global hits, misses
        # Local proxy: "GET http://host/path"  (the client knows about the proxy)
        # CDN:         "GET /path"             (the client thinks we ARE the site)
        url = self.path if self.path.startswith('http://') else ORIGIN + self.path

        if url in cache:
            hits += 1
            result = 'HIT'
        else:
            misses += 1
            result = 'MISS'
            with urllib.request.urlopen(url) as r:    # the proxy acts as a CLIENT
                cache[url] = (r.headers['Content-Type'], r.read())

        print(f'{result:4}  {url}   (hits={hits}, misses={misses})')
        content_type, body = cache[url]
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.send_header('X-Cache', result)
        self.send_header('Via', '1.1 proxy_cache')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):   # hide the default log: we print our own line
        pass

print('Proxy cache on http://localhost:8080 ...')
HTTPServer(('', 8080), Handler).serve_forever()
