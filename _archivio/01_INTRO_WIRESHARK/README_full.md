# 01 Introduction: what is really on the network

Reference: Kurose & Ross, *Computer Networking*, Ch. 1 (Sec. 1.2–1.6 and the Wireshark Labs)

## Concepts

1. A machine has **several addresses**, at different layers: **MAC** (link layer) and **IP** (network layer).
2. **RTT** (round-trip time) = time for a packet to go to a host and come back. It includes propagation, transmission and queuing delay.
3. The Internet core is an **interconnection of ISPs**: a path crosses routers of different organisations.
4. Every packet is **encapsulated**: Ethernet frame → IP datagram → TCP/UDP segment → application message.
5. A **sniffer** (tcpdump, Wireshark) reads everything on the medium: unencrypted traffic is readable by anyone who captures it.
6. **Average throughput** = F / T (bits transferred / time). End-to-end throughput = **min(Rs, Rc)**: the slowest link is the **bottleneck**.

## Files

| File | What it is |
|---|---|
| `test.pcap` | A ready capture, to use in Wireshark if you cannot capture yourself |

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

Remember the name of your real interface (here `enp1s0`): you need it in Step 4.

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

## Step 3. The routers on the path

**What it does:** `traceroute` lists the routers (**hops**) on the path to the destination, with the RTT to each one ([man page](https://man7.org/linux/man-pages/man8/traceroute.8.html)).

```bash
traceroute google.com
```

## Step 4. Capture everything

**What it does:** `tcpdump` captures the packets on an interface ([man page](https://www.tcpdump.org/manpages/tcpdump.1.html)). `-i` = interface to listen on (yours from Step 1). `-w` = write the packets to a file. `timeout 10` stops it after 10 seconds. `sudo` is needed to capture.

```bash
sudo timeout 10 tcpdump -i enp1s0 -w capture_all.pcap
```
While it captures, use the computer as usual: open a site, check your mail.

## Step 5. Open the capture in Wireshark

Copy `capture_all.pcap` to your computer (e.g. with `scp`) and open it with [Wireshark](https://www.wireshark.org/docs/wsug_html_chunked/). No capture? Use `test.pcap`.

## Step 6. Measure the throughput

**What it does:** curl downloads a 100 MB test file ([man page](https://curl.se/docs/manpage.html)). `-o /dev/null` = throw the file away. `-w` = print, at the end, the [write-out variables](https://curl.se/docs/manpage.html#-w) we choose: `%{size_download}` (bytes), `%{time_total}` (seconds), `%{speed_download}` (average bytes/s).

```bash
curl -o /dev/null -w "bytes downloaded: %{size_download}\ntime: %{time_total} s\naverage throughput: %{speed_download} B/s\n" http://ipv4.download.thinkbroadband.com/100MB.zip
```
**Output**
```
bytes downloaded: 104857600
time: 12.752198 s
average throughput: 8222707 B/s
```

## Step 7. Throughput with a limit

**What it does:** `--limit-rate 1M` = curl downloads at most 1 MB/s. Now **you** are the bottleneck (Rc), not the network.

```bash
curl --limit-rate 1M -o /dev/null -w "bytes downloaded: %{size_download}\ntime: %{time_total} s\naverage throughput: %{speed_download} B/s\n" http://ipv4.download.thinkbroadband.com/10MB.zip
```
**Output**
```
bytes downloaded: 10485760
time: 9.354948 s
average throughput: 1120878 B/s
```

---

## Questions

Answer by looking at the capture in Wireshark and at the outputs above.

**Q1.** Which protocols do you see in the "Protocol" column (ARP, DNS, TCP, UDP, TLS, mDNS...)? Did you expect so much "background" traffic?

**Q2.** Find a DNS request: which name is resolved, and which IP address comes back?

**Q3.** Find the first packets of a TCP connection, before any data. How long until the other end replies? Which delay of Sec. 1.4 is it?

**Q4.** Select a packet and look at the nested layers (Frame / Ethernet II / Internet Protocol / TCP or UDP / application). Match each one to a layer of the Internet stack (Sec. 1.5).

**Q5.** How much traffic is in clear text, and how much is encrypted (TLS)? What could someone capturing on a shared network see (Sec. 1.6)?

**Q6.** Is the RTT from ping (Step 2) consistent with the request/reply times you see in Wireshark?

**Q7.** Pick 2–3 middle hops from Step 3 (not the first, your home/campus router) and look up their IP on [ipinfo.io](https://ipinfo.io) or [bgp.he.net](https://bgp.he.net). Which ISP owns each one? Does it change along the path (Sec. 1.3)?

**Q8.** In Step 6, compute F/T by hand: does it match `average throughput`? Is it close to the nominal speed of your connection?

**Q9.** Run Step 6 without `-o /dev/null -w ...`: curl shows "Average Speed" and "Current Speed". Why are they different?

**Q10.** Step 7 vs Step 6: does the throughput get close to 1 MB/s or to the speed of your connection? Who is the bottleneck in the min(Rs, Rc) model (Fig. 1.19)?
