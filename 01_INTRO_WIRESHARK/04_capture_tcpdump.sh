#tcpdump: cattura TUTTO il traffico sull'interfaccia per pochi secondi (nessun filtro)
#sostituite INTERFACCIA con la vostra (vedi output_ipaddr.txt, es. eth0, enp0s1...)
#mentre cattura, usate normalmente il computer (aprite un sito, controllate la posta, ecc.)
#dopo 10 secondi si ferma da sola: aprite capture_all.pcap con Wireshark sul vostro PC

sudo timeout 10 tcpdump -i INTERFACCIA -w capture_all.pcap
