#!/bin/bash
#traceroute: lists the routers (hops) on the path to the destination and the delay (RTT)
#measured for each of them.
#Ref. Kurose, Ch.1 sec. 1.4 "Delay, Loss, and Throughput in Packet-Switched Networks"

traceroute google.com > output_traceroute.txt
