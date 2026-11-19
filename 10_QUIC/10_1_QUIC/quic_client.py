#!/usr/bin/env python
# QUIC client: send a file to quic_server.py; every 0.05 s save cwnd, ssthresh, RTT and acked bytes
#   python quic_client.py FILE ALGORITHM CSV      e.g.  python quic_client.py file.bin reno quic_reno.csv

import asyncio
import ssl
import sys
import time

from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration

FILE, CC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PACKET = 1200    # bytes of one QUIC packet (UDP payload)


async def main():
    data = open(FILE, "rb").read()
    config = QuicConfiguration(is_client=True, alpn_protocols=["file"], congestion_control_algorithm=CC)
    config.verify_mode = ssl.CERT_NONE    # do not check the server certificate

    start = time.time()
    async with connect("127.0.0.1", 12000, configuration=config) as client:
        print("connected in %.0f ms" % ((time.time() - start) * 1000))

        quic = client._quic                                  # the QUIC connection inside aioquic
        stream = quic.get_next_available_stream_id()
        quic.send_stream_data(stream, data, end_stream=True)  # the whole file on one stream
        sender = quic._streams[stream].sender
        client.transmit()

        out = open(OUT, "w")
        out.write("time,cwnd,ssthresh,rtt,bytes\n")
        start = time.time()
        while not sender.is_finished:                        # until the server has acked the whole file
            await asyncio.sleep(0.05)
            cwnd = quic._loss.congestion_window // PACKET
            ssthresh = (quic._loss._cc.ssthresh or 0) // PACKET     # None before the first loss
            rtt = quic._loss._rtt_smoothed * 1000                   # s -> ms
            acked = sender._buffer_start + sum(len(r) for r in sender._acked)    # in order + out of order
            out.write("%.3f,%d,%d,%.1f,%d\n" % (time.time(), cwnd, ssthresh, rtt, acked))
        out.close()

        seconds = time.time() - start
        print("%d bytes in %.1f s (%.2f Mbit/s), samples in %s" % (len(data), seconds, len(data) * 8 / seconds / 1e6, OUT))


asyncio.run(main())
