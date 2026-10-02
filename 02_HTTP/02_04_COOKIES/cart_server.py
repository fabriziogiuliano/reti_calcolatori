# A tiny shop: it remembers your cart thanks to a cookie.
#   /add?item=book  -> adds "book" to your cart
#   /cart           -> shows your cart
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

carts = {}        # the server's database: id -> list of items
next_id = 1678

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global next_id
        cookie = self.headers.get('Cookie')          # e.g. "id=1678" or None
        print('Cookie received:', cookie)
        cookies = SimpleCookie(cookie)               # "a=1; id=1678" -> {'a': '1', 'id': '1678'}
        user = cookies['id'].value if 'id' in cookies else None

        new = user not in carts
        if new:                                      # unknown customer: give a new id
            user = str(next_id)
            next_id += 1
            carts[user] = []

        url = urlparse(self.path)
        if url.path == '/add':                       # /add?item=book
            carts[user].append(parse_qs(url.query)['item'][0])

        self.send_response(200)
        if new:
            self.send_header('Set-Cookie', f'id={user}')
        self.end_headers()
        self.wfile.write(f"Customer {user}. Your cart: {carts[user]}\n".encode())

print('Shop on http://localhost:8000 ...')
HTTPServer(('', 8000), Handler).serve_forever()
