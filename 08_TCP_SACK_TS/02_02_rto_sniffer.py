#!/usr/bin/env python
# RTO sniffer: 02_01_ts_sniffer.py + SampleRTT from the timestamps and Jacobson's RTO

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
tsval_time = {} # dictionary: TSval of the client -> time (ms) the sniffer saw it
est = 0        # EstimatedRTT (ms)
dev = 0        # DevRTT (ms)
rto = 1000     # RTO (ms): 1 s before the first sample (RFC 6298)


def get_rto(sample):
    # Jacobson (Kurose Sec. 3.5.3): alpha = 1/8, beta = 1/4
    global est, dev
    if est == 0:                            # first sample
        est = sample
        dev = sample / 2
    else:
        est = 0.875 * est + 0.125 * sample
        dev = 0.75 * dev + 0.25 * abs(sample - est)
    return est + 4 * dev


def rto_show(pkt):
    global isn_c, isn_s, tsv_c, tsv_s, t_start, cport, est, dev, rto
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
        tsval_time.clear()
        est = 0
        dev = 0
        rto = 1000
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

    # SampleRTT = time of the ACK - time of the data segment whose TSval the ACK echoes in TSecr
    t = float(1000 * (pkt.time - t_start))
    if tcp.dport == PORT and len(tcp.payload) > 0 and tsval not in tsval_time:
        tsval_time[tsval] = t               # first data segment with this TSval
    if tcp.sport == PORT and tsecr in tsval_time:
        sample = t - tsval_time.pop(tsecr)  # pop: each TSval gives one sample only
        rto = get_rto(sample)

    print(f"ts:{round(1000*(pkt.time-t_start),2):05},SPORT:{tcp.sport:05},DPORT:{tcp.dport:05},S:{int(tcp.flags.S)},A:{int(tcp.flags.A)},F:{int(tcp.flags.F)},seq:{seq:05},ack:{ack:05},data_len:{len(tcp.payload)},TSval:{tsval:05},TSecr:{tsecr:05},RTO:{rto:07.1f}")


print("sniffing tcp port %d on %s" % (PORT, IFACE))
sniff(iface=IFACE, filter=FILTER, prn=rto_show, store=False)
