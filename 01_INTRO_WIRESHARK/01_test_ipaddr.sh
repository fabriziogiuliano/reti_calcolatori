#ip addr: elenca le interfacce di rete e gli indirizzi assegnati alla macchina
#(ifconfig è deprecato/non installato di default sulle distribuzioni recenti;
#il pacchetto net-tools è sostituito dal pacchetto iproute2, comando "ip")

ip addr > output_ipaddr.txt
