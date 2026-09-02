#!/bin/bash
#traceroute: elenca i router (hop) attraversati verso la destinazione e il ritardo (RTT)
#misurato per ciascuno di essi.
#Rif. Kurose, Cap.1 par. 1.4 "Ritardi, perdite e throughput nelle reti a commutazione di pacchetto"

traceroute google.com > output_traceroute.txt
