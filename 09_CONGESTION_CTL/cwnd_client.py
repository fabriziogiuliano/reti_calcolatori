#!/usr/bin/env python
# TCP client: send as fast as possible to tcp_server.py and log the congestion window

import argparse
import socket
import struct
import subprocess
import sys
import time

SERVER = ("127.0.0.1", 12000)
MSS = 1000

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--cc", default="cubic", help="congestion control, reno or cubic (Linux only)")
parser.add_argument("--time", type=float, default=30, help="seconds of sending")
parser.add_argument("--every", type=float, default=0.05, help="seconds between two cwnd samples")
parser.add_argument("--out", default="cwnd.csv", help="CSV file for the samples")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# choose the congestion control algorithm
if sys.platform == "linux":
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, args.cc.encode())
    cc = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, 16).strip(b"\0").decode()
else:
    # macOS: one switch for the whole system, 1 = newreno, 0 = cubic
    use_newreno = subprocess.check_output(["sysctl", "-n", "net.inet.tcp.use_newreno"]).strip()
    if use_newreno == b"1":
        cc = "newreno"
    else:
        cc = "cubic"
print("congestion control:", cc)

# small segments: without this, on the loopback (MTU 16 KB / 64 KB) we see only a few huge ones
try:
    # Linux: before connect, +12 bytes for the Timestamps option that it takes from each segment
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, MSS + 12)
    sock.connect(SERVER)
except OSError:
    sock.connect(SERVER)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, MSS)    # macOS: only after connect

# send() waits at most this long when the buffer is full: then we can take a sample
sock.settimeout(0.01)
data = b"x" * 65536

out = open(args.out, "w")
out.write("time,cwnd,ssthresh\n")
print("time,cwnd,ssthresh")
start = time.time()
next_sample = start
while time.time() - start < args.time:
    try:
        sock.send(data)
    except socket.timeout:
        pass
    if time.time() < next_sample:
        continue
    next_sample += args.every

    # read cwnd and ssthresh from the kernel
    if sys.platform == "linux":
        info = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 104)    # struct tcp_info
        ssthresh = struct.unpack_from("I", info, 76)[0]                     # in segments
        cwnd = struct.unpack_from("I", info, 80)[0]
    else:
        info = sock.getsockopt(socket.IPPROTO_TCP, 0x106, 112)    # TCP_CONNECTION_INFO
        ssthresh = struct.unpack_from("I", info, 20)[0] // MSS     # in bytes: to segments
        cwnd = struct.unpack_from("I", info, 24)[0] // MSS
    if ssthresh > 100000:    # "infinite" before the first loss
        ssthresh = 0

    # absolute time (Unix time): files of clients started at different moments line up
    line = "%.3f,%d,%d" % (time.time(), cwnd, ssthresh)
    out.write(line + "\n")
    print(line)

out.close()
sock.close()
print("samples saved in", args.out)
