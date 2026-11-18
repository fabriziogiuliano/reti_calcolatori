#!/usr/bin/env python
# Timestamps sniffer: one CSV-like line per TCP header, with the Timestamps option (TSval, TSecr)

import sys
from scapy.all import sniff, TCP

PORT = 12000
IFACE = "lo0" if sys.platform == "darwin" else "lo"
# Linux sees each loopback packet twice (out and in): keep only the incoming copy
FILTER = "tcp port %d" % PORT if sys.platform == "darwin" else "tcp port %d and inbound" % PORT

isn_c = 0      # ISN of the client (from the SYN)
isn_s = 0      # ISN of the server (from the SYN-ACK)
tsv_c = 0      # TSval of the client in the SYN
tsv_s = 0      # TSval of the server in the SYN-ACK
t_start = 0    # time of the SYN
cport = 0      # client port of the current connection


def ts_show(pkt):
    global isn_c, isn_s, tsv_c, tsv_s, t_start, cport
    tcp = pkt[TCP]
    # Timestamps option: TSval = clock of the sender (ms), TSecr = TSval of the other side, copied back
    tsval = 0
    tsecr = 0
    for name, value in tcp.options:         # options: list of (name, value)
        if name == "Timestamp":             # value = (TSval, TSecr)
            tsval = value[0]
            tsecr = value[1]

    if tcp.flags.S and not tcp.flags.A:     # SYN: new connection
        isn_c = tcp.seq
        tsv_c = tsval
        t_start = pkt.time
        cport = tcp.sport
    if tcp.flags.S and tcp.flags.A:         # SYN-ACK
        isn_s = tcp.seq
        tsv_s = tsval
    if cport not in (tcp.sport, tcp.dport): # packet of an old connection
        return

    # relative values: seq/ack from the ISN, TSval/TSecr from the clock in the SYN / SYN-ACK
    if tcp.dport == PORT:                   # client -> server
        seq = tcp.seq - isn_c
        ack = tcp.ack - isn_s
        tsval = tsval - tsv_c
        tsecr = tsecr - tsv_s
    else:                                   # server -> client
        seq = tcp.seq - isn_s
        ack = tcp.ack - isn_c
        tsval = tsval - tsv_s
        tsecr = tsecr - tsv_c
    if not tcp.flags.A:                     # no ACK flag (the SYN): ack and TSecr mean nothing
        ack = 0
        tsecr = 0

    print(f"ts:{round(1000*(pkt.time-t_start),2):05},SPORT:{tcp.sport:05},DPORT:{tcp.dport:05},S:{int(tcp.flags.S)},A:{int(tcp.flags.A)},F:{int(tcp.flags.F)},seq:{seq:05},ack:{ack:05},data_len:{len(tcp.payload)},TSval:{tsval:05},TSecr:{tsecr:05}")


print("sniffing tcp port %d on %s" % (PORT, IFACE))
sniff(iface=IFACE, filter=FILTER, prn=ts_show, store=False)
