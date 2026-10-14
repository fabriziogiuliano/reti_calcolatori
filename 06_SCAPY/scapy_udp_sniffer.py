#!/usr/bin/env python

from scapy.all import sniff, UDP

SERVER_PORT = 8888

IFACE = "lo0"

def analizza_pacchetto_udp(pkt):
    try:
        
        if UDP in pkt:
            # Estrai il livello UDP dal pacchetto
            if pkt[UDP].dport==SERVER_PORT:
                #pkt.show()
                print("---  UDP packet received ---")
                print(f"SRC port: {pkt[UDP].sport}")
                print(f"DST port: {pkt[UDP].dport}")
                print(f"Length: {pkt[UDP].len}")
                print(f"Checksum: {pkt[UDP].chksum} [0x{pkt[UDP].chksum:04x}]")
                print(f"Payload: {pkt[UDP].load}")
                print("----------------------------\n")
    except Exception as e:
        print(e)
        return

if __name__ == '__main__':
    #sniff(iface = "en0", filter="udp and port 8888", prn=analizza_pacchetto_udp)
    sniff(iface = IFACE, prn=analizza_pacchetto_udp)
