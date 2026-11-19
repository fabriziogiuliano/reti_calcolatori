#!/usr/bin/env python
# QUIC server: receive a file on UDP port 12000 and save it as received.bin

import asyncio

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived


class Receiver(QuicConnectionProtocol):
    data = b""

    # aioquic calls this function for every event of the connection
    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            self.data += event.data
            if event.end_stream:                     # the client said: the file is over
                open("received.bin", "wb").write(self.data)
                print("received %d bytes, saved in received.bin" % len(self.data))
                self.data = b""


async def main():
    config = QuicConfiguration(is_client=False, alpn_protocols=["file"])
    config.load_cert_chain("cert.pem", "key.pem")    # QUIC always encrypts: it needs a certificate
    await serve("127.0.0.1", 12000, configuration=config, create_protocol=Receiver)
    print("listening on 127.0.0.1:12000 (UDP)")
    await asyncio.Future()                           # run forever


asyncio.run(main())
