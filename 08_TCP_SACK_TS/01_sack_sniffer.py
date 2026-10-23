#!/usr/bin/env python
# SACK sniffer: one CSV-like line per segment, with the SACK blocks of the ACKs

import sys
from scapy.all import sniff, TCP

PORT = 12000
IFACE = "lo0" if sys.platform == "darwin" else "lo"

isn_c = 0      # ISN of the client (from the SYN)
isn_s = 0      # ISN of the server (from the SYN-ACK)
t_start = 0    # time of the SYN
cport = 0      # client port of the current connection


def sack_show(pkt):
    global isn_c, isn_s, t_start, cport
    tcp = pkt[TCP]

    # CONNECTION open / close (SYN, FIN): not explained yet, print only a text
    if tcp.flags.S:
        if tcp.flags.A:                     # SYN-ACK: ISN of the server
            isn_s = tcp.seq
        else:                               # SYN: ISN of the client
            isn_c, t_start, cport = tcp.seq, tcp.time, tcp.sport
            print("------- CONNECTION open -------")
        return
    if cport not in (tcp.sport, tcp.dport):           # packet of an old connection
        return
    if tcp.flags.F and tcp.dport == PORT:
        print("------- CONNECTION close -------")
    if len(tcp.payload) == 0 and (tcp.flags.F or tcp.dport == PORT):
        return                              # FIN, and client ACKs without data

    if tcp.dport == PORT:                   # client -> server
        seq, ack = tcp.seq - isn_c, tcp.ack - isn_s
    else:                                   # server -> client
        seq, ack = tcp.seq - isn_s, tcp.ack - isn_c
    if tcp.sport == PORT and ack <= 1:      # server ACK before any data (macOS window update)
        return

    line = f"ts:{round(1000*(tcp.time-t_start)):05},SPORT:{tcp.sport:05},DPORT:{tcp.dport:05},seq:{seq:05},ack:{ack:05},data_len:{len(tcp.payload)}"

    # SACK option: (left1, right1, left2, right2, ...), right edge excluded
    for name, value in tcp.options:
        if name == "SAck":
            line += ",SACK"
            for i in range(0, len(value), 2):
                line += f",SLE:{value[i] - isn_c:05},SRE:{value[i + 1] - isn_c:05}"
    print(line)


print("sniffing tcp port %d on %s" % (PORT, IFACE))
sniff(iface=IFACE, filter="tcp port %d" % PORT, prn=sack_show, store=False)
