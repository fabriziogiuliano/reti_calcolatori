from scapy.all import *
#from scapy.layers.inet import IP, UDP
#from scapy.layers.dns import DNS

target_ip = "unipa.it"
T=2
i=1
while True:
    pkt = IP(dst=target_ip,ttl=i) / UDP() 
    try:
        recv = sr1(pkt,timeout=T)
        print(recv.src)
        if recv.src == target_ip:
            break
    except Exception as e:
        continue
        #print(e)
    if i > 10:
        break
    i+=1