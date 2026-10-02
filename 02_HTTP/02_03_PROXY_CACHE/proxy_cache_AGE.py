# A caching PROXY for the local network: the browsers send ALL their requests here.
#   http  -> GET: HIT = answer from the cache, MISS = ask the origin, keep a copy, answer
#   https -> CONNECT: just a tunnel of encrypted bytes, nothing can be cached
import select
import socket
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time

cache = {}                  # url -> (content type, body)
hits = misses = 0
direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # we never use a proxy ourselves

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):                     # http: "GET http://host/path HTTP/1.1"
        global hits, misses
        url = self.path                   # the client sends the FULL url to a proxy
        MAX_AGE=2*60 #2 minutes
        if url in cache:
            t_now = time.time()
            t_age = t_now - cache[url][2]
            if t_age > MAX_AGE:
                print("remove url, AGE EXPIRED")
                cache.pop(url)

        if url in cache:
            hits += 1
            
            t_now = time.time()
            t_age = t_now - cache[url][2]
            result = f"HIT"
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

        print(f'{result:6}  {url}   (hits={hits}, misses={misses})')
        content_type, body, t_cache = cache[url]
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.send_header('X-Cache', result)
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

print('Proxy cache on http://localhost:8080 ...')
ThreadingHTTPServer(('', 8080), Handler).serve_forever()
