# proxy_cache_AGE.py, but a copy older than MAX_AGE is not thrown away: the proxy asks
# the origin "has it changed since my copy?" (conditional GET, If-Modified-Since).
#   304 Not Modified -> REVALIDATED: the copy is still good, its age starts again from 0
#   200 OK           -> MISS: the object changed, keep the new copy
import select
import socket
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_AGE = 30                # seconds: an older copy must be checked with the origin
cache = {}                  # url -> (content type, body, time of the copy, Last-Modified)
hits = misses = 0
direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # we never use a proxy ourselves

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):                     # http: "GET http://host/path HTTP/1.1"
        global hits, misses
        url = self.path                   # the client sends the FULL url to a proxy

        if url in cache and time.time() - cache[url][2] <= MAX_AGE:
            hits += 1
            result = 'HIT'                # young copy: answer at once
        else:
            headers = {}
            if url in cache and cache[url][3]:   # old copy: ask only if it changed
                headers['If-Modified-Since'] = cache[url][3]
            try:
                request = urllib.request.Request(url, headers=headers)
                with direct.open(request, timeout=10) as r:    # the proxy acts as a CLIENT
                    cache[url] = (r.headers['Content-Type'], r.read(), time.time(),
                                  r.headers['Last-Modified'])
                misses += 1
                result = 'MISS'
            except urllib.error.URLError as e:   # urllib treats 304 as an error too
                code = getattr(e, 'code', 502)
                if code != 304:           # origin error (e.g. 404) or unreachable (502)
                    print(f'{code}          {url}')
                    self.send_error(code)
                    return
                hits += 1
                result = 'REVALIDATED'    # not changed: keep the copy, reset its age
                content_type, body, _, last_modified = cache[url]
                cache[url] = (content_type, body, time.time(), last_modified)

        content_type, body, t_copy, _ = cache[url]
        age = int(time.time() - t_copy)
        print(f'{result:11}  {url}   (age={age}s, hits={hits}, misses={misses})')
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.send_header('X-Cache', result)
        self.send_header('Age', age)      # how many seconds old the copy is
        self.end_headers()
        self.wfile.write(body)

    def do_CONNECT(self):                 # https: "CONNECT host:443 HTTP/1.1"
        print(f'TUNNEL       {self.path}   (encrypted: cannot cache)')
        host, port = self.path.split(':')
        with socket.create_connection((host, int(port))) as remote:
            self.send_response(200, 'Connection established')
            self.end_headers()
            # From now on: copy bytes in both directions, we cannot read them
            sockets = [self.connection, remote]
            while True:
                readable, _, _ = select.select(sockets, [], [])
                for s in readable:
                    data = s.recv(65536)
                    if not data:
                        return
                    (remote if s is self.connection else self.connection).sendall(data)

    def log_message(self, *args):         # hide the default log: we print our own lines
        pass

print(f'Proxy cache on http://localhost:8080 (max age {MAX_AGE} s) ...')
ThreadingHTTPServer(('', 8080), Handler).serve_forever()
