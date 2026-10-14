#!/usr/bin/env python

import socket

host = '0.0.0.0'
data_payload = 2048


def echo_server(port):
    """ A simple echo server """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

    # Bind the socket to the port
    server_address = (host, port)
    print("Starting up echo server on %s port %s" % server_address)

    sock.bind(server_address)

    while True:
        print("Waiting to receive message from client")
        data, address = sock.recvfrom(data_payload)
        print("========")
        print(data)
        print("-- received %s bytes from %s" % (len(data), address))
        print("========")
        #print("-- Data: %s" % data)

        # if data:
        #     sent = sock.sendto(data.upper(), address)
        #     print("sent %s bytes back                    to %s" % (sent, address))


if __name__ == '__main__':
    """
    parser = argparse.ArgumentParser(description='Socket Server Example')
    parser.add_argument('--port', action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    """
    echo_server(8888)

