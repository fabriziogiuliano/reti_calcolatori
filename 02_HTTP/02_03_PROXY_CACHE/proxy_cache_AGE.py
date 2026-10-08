# proxy_cache.py + one rule: a copy is good only for MAX_AGE seconds, then it is thrown away.
#   http  -> GET: HIT = answer from the cache, MISS = ask the origin, keep a copy, answer
#   https -> CONNECT: just a tunnel of encrypted bytes, nothing can be cached
import select
import socket
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_AGE = 30                # seconds: an older copy is thrown away
cache = {}                  # url -> (content type, body, time of the copy)
hits = misses = 0
direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # we never use a proxy ourselves

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):                     # http: "GET http://host/path HTTP/1.1"
        global hits, misses
        url = self.path                   # the client sends the FULL url to a proxy

        if url in cache and time.time() - cache[url][2] > MAX_AGE:
            print(f'EXPIRED {url}')
            del cache[url]                # too old: throw it away

        if url in cache:
            hits += 1
            result = 'HIT'
        else:
            misses += 1
            result = 'MISS'
            try:
                with direct.open(url, timeout=10) as r:    # the proxy acts as a CLIENT
                    cache[url] = (r.headers['Content-Type'], r.read(), time.time())
            except urllib.error.URLError as e:   # origin error (e.g. 404) or unreachable (502)
                code = getattr(e, 'code', 502)
                print(f'{code}     {url}')
                self.send_error(code)
                return

        content_type, body, t_copy = cache[url]
        age = int(time.time() - t_copy)
        print(f'{result:6}  {url}   (age={age}s, hits={hits}, misses={misses})')
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.send_header('X-Cache', result)
        self.send_header('Age', age)      # how many seconds old the copy is
        self.end_headers()
        self.wfile.write(body)

    def do_CONNECT(self):                 # https: "CONNECT host:443 HTTP/1.1"
        print(f'TUNNEL  {self.path}   (encrypted: cannot cache)')
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
