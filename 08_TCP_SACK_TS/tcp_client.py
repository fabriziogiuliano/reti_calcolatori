#!/usr/bin/env python
# TCP client: send a stream of chunks to tcp_server.py

import argparse
import socket
import sys
import time

SERVER = ("127.0.0.1", 12000)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--n", type=int, default=200, help="chunks to send")
parser.add_argument("--size", type=int, default=1000, help="bytes per chunk, also the MSS (min 536)")
parser.add_argument("--interval", type=float, default=0, help="seconds between chunks (0 = all at once)")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()
N, SIZE, INTERVAL = args.n, args.size, args.interval

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# send each chunk at once, do not wait to fill a segment (no Nagle)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

# small segments: without this, on the loopback (MTU 16 KB / 64 KB) we see only a few huge ones
# the kernel refuses a too small MSS: use at least 536, the classic default
MSS = max(SIZE, 536)
try:
    # Linux: before connect, +12 bytes for the Timestamps option that it takes from each segment
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, MSS + 12)
    sock.connect(SERVER)
except OSError:
    sock.connect(SERVER)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, MSS)    # macOS: only after connect
print("MSS: %d bytes" % sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG))

start = time.time()
for i in range(N):
    sock.sendall(bytes([65 + i % 26]) * SIZE)    # AAAA..., BBBB..., ...
    time.sleep(INTERVAL)
# sendall() returns when the data is in the kernel buffer, not when it is delivered
print("handed %d chunks of %d bytes to TCP in %.2f s" % (N, SIZE, time.time() - start))

sock.shutdown(socket.SHUT_WR)    # FIN: no more data from the client
sock.settimeout(10)
try:
    sock.recv(1)                 # returns when the server closes: it got everything
    print("all data delivered after %.2f s" % (time.time() - start))
except socket.timeout:
    print("after 10 s data still not delivered: TCP is still retransmitting")
except OSError as e:
    print("connection lost: %s" % e)     # TCP gave up (timeout / reset)
sock.close()
