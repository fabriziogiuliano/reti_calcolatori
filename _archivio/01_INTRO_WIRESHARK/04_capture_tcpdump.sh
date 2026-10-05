#tcpdump: captures ALL the traffic on the interface for a few seconds (no filter)
#replace INTERFACE with yours (see output_ipaddr.txt, e.g. eth0, enp0s1...)
#while it captures, use the computer as usual (open a site, check your mail, etc.)
#it stops by itself after 10 seconds: open capture_all.pcap with Wireshark on your PC

sudo timeout 10 tcpdump -i INTERFACE -w capture_all.pcap
