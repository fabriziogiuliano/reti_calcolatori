#!/usr/bin/env python
# SACK sniffer: one CSV-like line per TCP header, with the SACK blocks

import sys
from scapy.all import sniff, TCP

PORT = 12000
IFACE = "lo0" if sys.platform == "darwin" else "lo"

isn_c = 0      # ISN of the client (from the SYN)
isn_s = 0      # ISN of the server (from the SYN-ACK)
t_start = 0    # time of the SYN
cport = 0      # client port of the current connection
ws_c = 0       # window scale of the client (from the SYN)
ws_s = 0       # window scale of the server (from the SYN-ACK)


def sack_show(pkt):
    global isn_c, isn_s, t_start, cport, ws_c, ws_s
    tcp = pkt[TCP]

    if tcp.flags.S and not tcp.flags.A:     # SYN: new connection, ISN of the client
        isn_c, t_start, cport = tcp.seq, tcp.time, tcp.sport
        ws_c = dict(tcp.options).get("WScale", 0)
    if tcp.flags.S and tcp.flags.A:         # SYN-ACK: ISN of the server
        isn_s = tcp.seq
        ws_s = dict(tcp.options).get("WScale", 0)
    if cport not in (tcp.sport, tcp.dport): # packet of an old connection
        return

    if tcp.dport == PORT:                   # client -> server
        seq, ack, ws = tcp.seq - isn_c, tcp.ack - isn_s, ws_c
    else:                                   # server -> client
        seq, ack, ws = tcp.seq - isn_s, tcp.ack - isn_c, ws_s
    if not tcp.flags.A:                     # no ACK flag (the SYN): the ack field means nothing
        ack = 0
    # receive window in bytes = window field x 2^scale (never scaled in SYN and SYN-ACK)
    win = tcp.window if tcp.flags.S else tcp.window << ws

    line = f"ts:{round(1000*(tcp.time-t_start)):05},SPORT:{tcp.sport:05},DPORT:{tcp.dport:05},S:{int(tcp.flags.S)},A:{int(tcp.flags.A)},F:{int(tcp.flags.F)},seq:{seq:05},ack:{ack:05},win:{win:07},data_len:{len(tcp.payload)}"

    # SACK option: (left1, right1, left2, right2, ...), right edge excluded
    for name, value in tcp.options:
        if name == "SAck":
            line += ",SACK"
            for i in range(0, len(value), 2):
                line += f",SLE:{value[i] - isn_c:05},SRE:{value[i + 1] - isn_c:05}"
    print(line)


print("sniffing tcp port %d on %s" % (PORT, IFACE))
sniff(iface=IFACE, filter="tcp port %d" % PORT, prn=sack_show, store=False)
