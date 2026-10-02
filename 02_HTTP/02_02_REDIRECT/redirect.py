# A minimal client that follows redirects, like a browser does.
# Run: python redirect.py http://localhost:8000/a     (default: http://google.com)
import socket
import ssl
import sys
from urllib.parse import urlparse, urljoin

url = sys.argv[1] if len(sys.argv) > 1 else 'http://google.com'
MAX_REDIRECTS = 5

for hop in range(MAX_REDIRECTS + 1):
    # 1. Split the URL: scheme, host, port, path
    u = urlparse(url)
    port = u.port or (443 if u.scheme == 'https' else 80)
    path = u.path or '/'

    # 2. A NEW TCP connection for every hop (+ TLS if https)
    sock = socket.create_connection((u.hostname, port))
    if u.scheme == 'https':
        sock = ssl.create_default_context().wrap_socket(sock, server_hostname=u.hostname)

    # 3. Send the request and read the whole response
    sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {u.netloc}\r\nConnection: close\r\n\r\n".encode())
    response = b''
    while chunk := sock.recv(4096):
        response += chunk
    sock.close()

    # 4. Status line + headers (we ignore the body)
    status_line, *header_lines = response.split(b'\r\n\r\n')[0].decode().split('\r\n')
    headers = {k.strip().lower(): v.strip() for k, v in (h.split(':', 1) for h in header_lines)}
    status = int(status_line.split(' ')[1])
    print(f"[{hop}] GET {url}\n    <- {status_line}")

    # 5. 3xx: read Location and try again. Anything else: stop.
    if 300 <= status < 400:
        print(f"    Location: {headers['location']}")
        url = urljoin(url, headers['location'])   # "/b" -> "http://localhost:8000/b"
    else:
        break
else:
    print(f"STOP: more than {MAX_REDIRECTS} redirects. Is it a loop?")
