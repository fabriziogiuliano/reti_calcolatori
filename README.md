# Computer Networks – Lab

Lab material for *Computer Networking* (Kurose & Ross). Each folder is one lab: its README.md has the steps; where there is an exercise for students, it is in the subfolder `EXERCISES/` of the lab.

## Before the first lab

Follow [00_PYTHON_ENVIRONMENT_SETUP](00_PYTHON_ENVIRONMENT_SETUP/): it installs conda and creates the environment `reti_calcolatori` (Python 3.11).

From lab 08 on, the labs emulate a slow or lossy link with `tc` on the loopback ([`emulate_channel.sh`](09_CONGESTION_CTL/emulate_channel.sh)): they need `sudo`.

Lab 12 (network emulation with Containernet) has its own installation and its own conda environment, `cn`: see [12_CONTAINERNET](12_CONTAINERNET/).

## Labs

**Tools and application layer** (Kurose & Ross, Ch. 1-2)

| Folder | Topic | Exercise |
|---|---|---|
| [00_PYTHON_ENVIRONMENT_SETUP](00_PYTHON_ENVIRONMENT_SETUP/) | conda, the `reti_calcolatori` environment | – |
| [01_INTRO_WIRESHARK](01_INTRO_WIRESHARK/) | ip addr, ping | – |
| [02_HTTP/02_00_CURL](02_HTTP/02_00_CURL/) | curl options | status codes |
| [02_HTTP/02_01_SIMPLE](02_HTTP/02_01_SIMPLE/) | GET with a raw socket | – |
| [02_HTTP/02_02_REDIRECT](02_HTTP/02_02_REDIRECT/) | 3xx + Location | your own redirect chain |
| [02_HTTP/02_03_PROXY_CACHE](02_HTTP/02_03_PROXY_CACHE/) | proxy cache | a new object in the cache |
| [02_HTTP/02_04_COOKIES](02_HTTP/02_04_COOKIES/) | cookies, cart | change the customer numbers |
| [02_HTTP/02_05_PERSISTENT_HTTP](02_HTTP/02_05_PERSISTENT_HTTP/) | HTTP/1.0 vs 1.1 | a slower network |
| [02_HTTP/02_06_HTTP_HOL](02_HTTP/02_06_HTTP_HOL/) | HOL blocking, HTTP/2 | a fourth object |
| [03_SMTP](03_SMTP/) | SMTP by hand | change the receiver |
| [04_DNS](04_DNS/) | dig, records, cache | who handles the mail of a domain? |

**Transport layer** (Kurose & Ross, Ch. 3)

| Folder | Topic | Exercise |
|---|---|---|
| [05_SOCKET](05_SOCKET/) | UDP sockets with ncat, lsof, tcpdump | – |
| [06_SCAPY](06_SCAPY/) | forging packets with Scapy | break the UDP checksum |
| [07_RDT](07_RDT/) | RDT 3.0 (stop-and-wait) on top of UDP | – |
| [08_TCP_SACK_TS](08_TCP_SACK_TS/) | TCP SACK and Timestamps, Karn and Jacobson | – |
| [09_CONGESTION_CTL](09_CONGESTION_CTL/) | TCP congestion control on an emulated bottleneck: NewReno, Cubic, BBR, and who gets the link | – |
| [10_PERFORMANCE_IPERF](10_PERFORMANCE_IPERF/) | iperf, TCP vs UDP: rate, RTT, queue size, bufferbloat, BBR vs Cubic | – |
| [11_QUIC/11_1_QUIC](11_QUIC/11_1_QUIC/) | QUIC, a reliable transport on UDP: streams, Reno vs Cubic | – |

**Network layer: emulation and SDN** (Kurose & Ross, Ch. 4-5)

| Folder | Topic | Exercise |
|---|---|---|
| [12_CONTAINERNET](12_CONTAINERNET/) | emulated networks of hosts, switches and routers: OpenFlow, SDN controllers, network monitoring, OSPF | in each lab |
