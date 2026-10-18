#!/usr/bin/env python
# RDT 3.0 receiver, on top of UDP

import argparse
import logging
import random
import socket
import sys
import time

PORT = 9999

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--rtt", type=float, default=0.1, help="round-trip time in seconds (waited before each ACK)")
parser.add_argument("--loss", type=float, default=0, help="probability of losing a packet")
parser.add_argument("--corrupt", type=float, default=0, help="probability of flipping one bit")
parser.add_argument("--c", type=float, default=1e9, help="link capacity, bit/s")
parser.add_argument("--verbose", action="store_true", help="also log the FSM states")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

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
sock.bind(("0.0.0.0", PORT))
print("Receiver waiting on UDP port", PORT)

expected = 0    # the seq we are waiting for: 0, 1, 0, 1, ...
while True:
    logging.debug("[Wait for %d from below]", expected)
    pkt, sender = sock.recvfrom(2048)

    if random.random() < args.loss:
        logging.info("    DATA lost: no ACK")
        continue

    if random.random() < args.corrupt:
        pkt = pkt[:3] + bytes([pkt[3] ^ 1]) + pkt[4:]   # flip one bit of the data

    if is_ok(pkt) and pkt[0] == expected:
        logging.info("    DATA %d received: deliver %d bytes", pkt[0], len(pkt) - 3)
        expected = 1 - expected
    else:
        logging.info("    corrupted or duplicate DATA: send the last ACK again")

    # time.sleep(args.rtt)    # imprecise: the OS wakes us up late (+4 ms on macOS)
    wait(args.rtt)
    # ACK the last packet received correctly
    ack = make_pkt(1 - expected, b"")
    wait(len(ack) * 8 / args.c)    # transmission time of the ACK
    sock.sendto(ack, sender)
    logging.debug("    ACK %d sent", ack[0])
