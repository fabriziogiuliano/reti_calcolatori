#!/usr/bin/env python
# TCP sink: accept many connections at the same time, read everything, count the bytes

import socket
import threading

SERVER = ("127.0.0.1", 12000)


def receive(conn, addr):
    # runs in its own thread: one per connection
    conn.settimeout(10)
    total = 0
    try:
        while True:
            data = conn.recv(65536)
            if not data:        # the client closed the connection (FIN)
                break
            total += len(data)
        print("%s:%d sent %d bytes" % (addr[0], addr[1], total))
    except socket.timeout:
        print("%s:%d no data for 10 s after %d bytes: client gone? the connection is hanging (half-open)"
              % (addr[0], addr[1], total))
    except OSError as e:
        print("%s:%d connection lost after %d bytes: %s" % (addr[0], addr[1], total, e))
    conn.close()


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(SERVER)
sock.listen()
print("listening on %s:%d" % SERVER)

while True:
    conn, addr = sock.accept()
    print("%s:%d connected" % addr)
    # a new thread reads this connection, the loop goes back to accept() at once
    threading.Thread(target=receive, args=(conn, addr), daemon=True).start()
