# 01 Introduction: what is really on the network

Reference: Kurose & Ross, *Computer Networking*, Ch. 1 (Sec. 1.2, 1.4)

## Concepts

1. A machine has **several addresses**, at different layers: **MAC** (link layer) and **IP** (network layer).
2. **RTT** (round-trip time) = time for a packet to go to a host and come back. It includes propagation, transmission and queuing delay.

---

## Step 1. Interfaces and addresses

**What it does:** `ip addr` lists the network interfaces and their addresses ([man page](https://man7.org/linux/man-pages/man8/ip-address.8.html)). `ifconfig` is the old command, no longer installed by default.

```bash
ip addr
```
**Output**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
    inet6 ::1/128 scope host noprefixroute
2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether ac:b4:80:40:75:c7 brd ff:ff:ff:ff:ff:ff
    inet 10.8.8.40/16 brd 10.8.255.255 scope global dynamic enp1s0
    inet6 fe80::9e9e:8715:942d:ec2/64 scope link noprefixroute
```

| Field | Meaning |
|---|---|
| `lo`, `enp1s0` | Interface name. `lo` = loopback, the machine itself (127.0.0.1) |
| `UP`, `BROADCAST`, `MULTICAST` | The interface is active, and which kinds of sending it supports |
| `mtu` | Max data size in one packet |
| `link/ether` | **MAC** address (link layer) |
| `inet` | **IPv4** address + mask (e.g. `/16`) |
| `inet6` | **IPv6** address |
| `scope` | Who sees the address: `host` = this machine, `link` = local network, `global` = everyone |

## Step 2. RTT with ping

**What it does:** `ping` sends small packets to a host and measures the RTT of each one ([man page](https://man7.org/linux/man-pages/man8/ping.8.html)). `-c 5` = send 5 packets, then stop.

```bash
ping -c 5 google.com
```
**Output**
```
PING google.com (142.250.180.174): 56 data bytes
64 bytes from 142.250.180.174: icmp_seq=0 ttl=114 time=30.421 ms
64 bytes from 142.250.180.174: icmp_seq=1 ttl=114 time=30.904 ms
...
round-trip min/avg/max/stddev = 30.421/30.820/31.290/0.300 ms
```
