#!/usr/bin/env python
# RDT 3.0 sender (stop-and-wait), on top of UDP

import argparse
import logging
import os
import socket
import sys
import time

RECEIVER = ("127.0.0.1", 9999)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--n", type=int, default=10, help="packets to send")
parser.add_argument("--size", type=int, default=1000, help="data bytes per packet")
parser.add_argument("--timeout", type=float, default=0.5, help="seconds before a retransmission")
parser.add_argument("--c", type=float, default=1e9, help="link capacity, bit/s")
parser.add_argument("--verbose", action="store_true", help="also log the FSM states")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()
N, SIZE, TIMEOUT, C = args.n, args.size, args.timeout, args.c

# every log line starts with the ms elapsed since the script started
logging.basicConfig(format="%(relativeCreated)9.1f ms  %(message)s",
                    level=logging.DEBUG if args.verbose else logging.INFO)


def wait(t):
    # precise wait: check the clock in a loop (uses 100% of a CPU core)
    end = time.perf_counter() + t
    while time.perf_counter() < end:
        pass


def checksum(data):
    return sum(data) % 65536


def make_pkt(seq, data):
    # RDT packet = seq (1 byte) + checksum (2 bytes) + data
    return bytes([seq]) + checksum(bytes([seq]) + data).to_bytes(2, "big") + data


def is_ok(pkt):
    return int.from_bytes(pkt[1:3], "big") == checksum(pkt[0:1] + pkt[3:])


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(TIMEOUT)

seq = 0
retransmissions = 0
start = time.time()

for i in range(N):
    logging.debug("[Wait for call %d from above] send DATA %d", seq, seq)
    pkt = make_pkt(seq, os.urandom(SIZE))
    #time.sleep(len(pkt) * 8 / C)    # emulated transmission time L/C
    wait(len(pkt) * 8 / C)
    sock.sendto(pkt, RECEIVER)

    # stop and wait: nothing else is sent until the right ACK arrives
    logging.debug("[Wait for ACK %d]", seq)
    while True:
        try:
            ack, _ = sock.recvfrom(2048)
            if is_ok(ack) and ack[0] == seq:
                logging.debug("    ACK %d received", seq)
                break
            logging.info("    wrong ACK: ignore it")
        except socket.timeout:
            logging.info("    timeout: resend DATA %d", seq)
            #time.sleep(len(pkt) * 8 / C)
            wait(len(pkt) * 8 / C)
            sock.sendto(pkt, RECEIVER)
            retransmissions += 1

    seq = 1 - seq

elapsed = time.time() - start
throughput = N * SIZE * 8 / elapsed

print("sent %d packets of %d bytes in %.2f s" % (N, SIZE, elapsed))
print("retransmissions: %d" % retransmissions)
print("time per packet: %.3f ms" % (elapsed / N * 1000))
print("throughput: %.2f Mbit/s" % (throughput / 1e6))
print("utilization of a %g bit/s link: %.3f %%" % (C, throughput / C * 100))
