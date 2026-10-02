# The same redirect server, written with bare sockets: no library hides anything.
# Run: python redirect_server_raw.py    (stop redirect_server.py first: same port)
import socket

# path -> (status line, where to go next)
ROUTES = {
    '/a':    ('301 Moved Permanently', '/b'),
    '/b':    ('302 Found', '/c'),
    '/loop': ('302 Found', '/loop'),
}

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('', 8000))   # the client did connect(), the server does bind() + listen() + accept()
srv.listen()
print('Listening on http://localhost:8000 ...')

while True:
    conn, addr = srv.accept()
    request = conn.recv(4096).decode()
    request_line = request.split('\r\n')[0]   # "GET /a HTTP/1.1"
    path = request_line.split(' ')[1]         # "/a"
    print(addr, request_line)

    if path in ROUTES:
        status, location = ROUTES[path]
        response = f"HTTP/1.1 {status}\r\nLocation: {location}\r\nContent-Length: 0\r\n\r\n"
    elif path == '/c':
        body = '<h1>You made it!</h1>'
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(body)}\r\n\r\n{body}"
    else:
        response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"

    conn.sendall(response.encode())
    conn.close()
