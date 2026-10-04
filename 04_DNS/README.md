# DNS from the shell (Linux / macOS)

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.4)

Linux install: `sudo apt install dnsutils` (macOS: already installed)

Two tools are enough: `host` (simple answers) and `dig` (shows the DNS records).

### The `dig` options used in this lab

A `dig` command is: `dig [options] name [type]`. The options that start with `+` choose **what to print** or **how to ask**.

| Option | What it does | First used in |
|---|---|---|
| `+noall` | print **nothing** (used together with the next one) | 3 |
| `+answer` | print only the **ANSWER** section: the records we asked for | 3 |
| `+short` | print only the **Value** of the records, nothing else | 4 |
| `A`, `AAAA`, `NS`, `MX`, `CNAME`, `TXT` | the **type** of record to ask for (default: `A`) | 4 |
| `-x 8.8.8.8` | reverse lookup: ask for the **name** of an IP address (type PTR) | 4 |
| `+stats` | also print some statistics: the **Query time** and the **SERVER** that answered | 5 |
| `.` (as the name) | the **root** of the DNS tree | 6 |
| `+trace` | do not ask the local DNS server: start from the **root** servers and follow the hierarchy step by step, printing every answer | 6 |

`dig +noall +answer` and `dig +short` both cut the output: the first keeps the full records (Name, TTL, Class, Type, Value), the second only the values. Without options `dig` prints everything (header, question, answer, statistics): try `dig gaia.cs.umass.edu` once to see it.

Online: [how to use dig](https://jvns.ca/blog/2021/12/04/how-to-use-dig/) (a friendly guide) and the [dig manual](https://linux.die.net/man/1/dig) (or `man dig` in the terminal).

---

## 1. Who resolves names for my machine?

> Before asking DNS, the system looks in a local file. Then it asks its local DNS server.

### Command

**What it does:** Prints the local file with the names the machine knows without DNS.

```bash
cat /etc/hosts
```
**Expected output**
```
127.0.0.1	localhost
255.255.255.255	broadcasthost
::1             localhost
```
`localhost` is the machine itself: `127.0.0.1` in IPv4, `::1` in IPv6. A name written here is used instead of DNS, on this machine only.

### Command

**What it does:** Shows which DNS server this machine sends its questions to.

```bash
cat /etc/resolv.conf
```
**Expected output**
```
search homenet.telecomitalia.it
nameserver 192.168.1.1
```
`nameserver` is the **local DNS server**: every question goes there first. At home it is the router (`192.168.1.1`). In the lab it is the university DNS server.

*Linux note:* if you see `nameserver 127.0.0.53`, run `resolvectl status` and read the line `Current DNS Server` to find the real one.

---

## 2. From a name to an address

> The basic job of DNS: you give a name, you get an IP address.

### Command

**What it does:** Asks DNS for the address of `www.unipa.it`.

```bash
host www.unipa.it
```
**Expected output**
```
www.unipa.it has address 147.163.149.59
www.unipa.it has address 147.163.149.60
```
One name, two addresses: the web site runs on two servers and DNS gives both, so the visitors are shared between them.

### Command

**What it does:** Asks the same question for the domain `unipa.it`.

```bash
host unipa.it
```
**Expected output**
```
unipa.it has address 147.163.149.59
unipa.it mail is handled by 0 unipa-it.mail.protection.outlook.com.
```
DNS stores more than addresses. The second line says which server receives the e-mail for `@unipa.it`: a Microsoft server (outlook.com).

---

## 3. What a DNS record looks like

> DNS answers are made of **resource records**. Each record has four parts: Name, TTL, Type, Value.

### Command

**What it does:** Asks for the address of `gaia.cs.umass.edu` and prints the full record.

```bash
dig +noall +answer gaia.cs.umass.edu
```
**Expected output**
```
gaia.cs.umass.edu.	3600	IN	A	128.119.245.12
```
Read it from left to right:

- **Name**: `gaia.cs.umass.edu.`
- **TTL**: `3600` seconds. The answer can be kept in a cache for one hour.
- **Class**: `IN` (Internet). It is always IN: ignore it.
- **Type**: `A` = an IPv4 address.
- **Value**: `128.119.245.12`

---

## 4. The main record types

> The Type says what kind of information the record holds. Here `+short` prints only the Value.

### Command

**What it does:** Asks for the IPv4 address (type A).

```bash
dig +short A gaia.cs.umass.edu
```
**Expected output**
```
128.119.245.12
```
Type **A**: name → IPv4 address. The same value seen in exercise 3.

### Command

**What it does:** Asks for the IPv6 addresses (type AAAA).

```bash
dig +short AAAA google.com
```
**Expected output**
```
2a00:1450:4025:1803::8b
2a00:1450:4025:1803::64
2a00:1450:4025:1803::66
2a00:1450:4025:1803::8a
```
Type **AAAA**: name → IPv6 address. Your addresses may be different: Google answers with servers close to you.

### Command

**What it does:** Asks which DNS servers are responsible for `umass.edu` (type NS).

```bash
dig +short NS umass.edu
```
**Expected output**
```
ns1.umass.edu.
ns2.umass.edu.
ns3.umass.edu.
```
Type **NS**: the **authoritative** name servers of the domain, the ones that hold its official records. There are three, so one can fail without problems.

### Command

**What it does:** Asks which server receives the e-mail for `@umass.edu` (type MX).

```bash
dig +short MX umass.edu
```
**Expected output**
```
5 umass-edu.mail.protection.outlook.com.
```
Type **MX**: the mail server of the domain. `5` is the priority: with several mail servers, the lowest number is tried first.

### Command

**What it does:** Asks whether `www.amazon.com` is a nickname for another name (type CNAME).

```bash
dig +short CNAME www.amazon.com
```
**Expected output**
```
tp.47cf2c8c9-frontier.amazon.com.
```
Type **CNAME**: `www.amazon.com` is an **alias**. The real (canonical) name of the server is the one in the answer. The easy name stays the same even if the real server changes.

### Command

**What it does:** The opposite question: from an IP address to a name (type PTR).

```bash
dig +short -x 8.8.8.8
```
**Expected output**
```
dns.google.
```
Type **PTR**: address → name (reverse lookup). `8.8.8.8` is Google's public DNS server.

### Command

**What it does:** Asks for the text records of `unipa.it` (type TXT) and keeps only the SPF one.

```bash
dig +short TXT unipa.it | grep spf
```
**Expected output**
```
"v=spf1 include:_spf.google.com include:_spf.cineca.it include:spf.protection.outlook.com ip4:147.163.149.30 ip4:147.163.149.32 ip4:147.163.149.91 ip4:147.163.149.107 ip4:147.163.149.117 ip4:147.163.149.119 ip4:147.163.149.127 ip4:147.163.149.129 -all"
```
Type **TXT**: free text. This one is **SPF** (Sender Policy Framework): the list of mail servers allowed to send e-mail as `@unipa.it` (Google, Cineca, Outlook and some university addresses). `-all` = reject every other server. This is how a mail server can catch the fake sender of the SMTP lab (`03_SMTP`, Step 8).

---

## 5. Caching

> The **local DNS server** remembers every answer for TTL seconds: if someone asks the same name again, it answers from its cache without asking anybody else.

`dig` asks the local DNS server directly (the `SERVER` line below: the home router, or the university DNS server in the lab). So here we observe **its** cache.

### Command

**What it does:** Asks for the address of `www.cs.umass.edu` and also prints how long the answer took (`+stats`).

```bash
dig +noall +answer +stats www.cs.umass.edu
```
**Expected output**
```
www.cs.umass.edu.	450	IN	A	128.119.240.9
;; Query time: 124 msec
;; SERVER: 192.168.1.1#53(192.168.1.1)
...
```
124 ms: the local DNS server did not know the name, so it had to ask the other DNS servers (root, `.edu`, `umass.edu`).

### Command (run it again after a few seconds)

**What it does:** Exactly the same question, a second time.

```bash
dig +noall +answer +stats www.cs.umass.edu
```
**Expected output**
```
www.cs.umass.edu.	445	IN	A	128.119.240.9
;; Query time: 8 msec
;; SERVER: 192.168.1.1#53(192.168.1.1)
...
```
Compare the two outputs:
- the **Query time** drops to a few ms: the answer came from the cache, nobody else was asked;
- the **TTL is lower** (450 → 445): it is a countdown. When it reaches 0 the record is deleted from the cache, and the next question goes out again.

> In the lab, a classmate may have asked the same name a moment before you: then your **first** query is already fast. Try a name nobody asked, e.g. `www.math.umass.edu`.

---

## 6. The DNS hierarchy

> No single server knows every name. DNS is a tree: **root** servers → **TLD** servers (`.edu`, `.it`, `.com`) → **authoritative** servers of each domain.

### Command

**What it does:** Lists the root servers, the top of the tree.

```bash
dig . NS +short
```
**Expected output**
```
c.root-servers.net.
j.root-servers.net.
h.root-servers.net.
b.root-servers.net.
m.root-servers.net.
f.root-servers.net.
e.root-servers.net.
d.root-servers.net.
a.root-servers.net.
i.root-servers.net.
g.root-servers.net.
l.root-servers.net.
k.root-servers.net.
```
The 13 root servers, named from `a` to `m`.

### Command

**What it does:** Follows the whole path, step by step: root → `.edu` → `umass.edu` → answer.

```bash
dig +trace gaia.cs.umass.edu
```
> **Note:** In the lab, the university firewall blocks DNS queries (port 53) to external servers and only lets the official university resolvers go out. `dig +trace` has to query the root servers directly, so it times out. Try it from home.

**Expected output OUT OF THE LAB**
```
; <<>> DiG 9.10.6 <<>> +trace gaia.cs.umass.edu
;; global options: +cmd
.			450	IN	NS	f.root-servers.net.
.			450	IN	NS	g.root-servers.net.
.			450	IN	NS	h.root-servers.net.
.			450	IN	NS	i.root-servers.net.
.			450	IN	NS	j.root-servers.net.
.			450	IN	NS	k.root-servers.net.
.			450	IN	NS	l.root-servers.net.
.			450	IN	NS	m.root-servers.net.
.			450	IN	NS	a.root-servers.net.
.			450	IN	NS	b.root-servers.net.
.			450	IN	NS	c.root-servers.net.
.			450	IN	NS	d.root-servers.net.
.			450	IN	NS	e.root-servers.net.
;; Received 811 bytes from 192.168.1.1#53(192.168.1.1) in 23 ms

edu.			172800	IN	NS	c.edu-servers.net.
edu.			172800	IN	NS	m.edu-servers.net.
edu.			172800	IN	NS	a.edu-servers.net.
edu.			172800	IN	NS	e.edu-servers.net.
edu.			172800	IN	NS	g.edu-servers.net.
edu.			172800	IN	NS	i.edu-servers.net.
edu.			172800	IN	NS	b.edu-servers.net.
edu.			172800	IN	NS	d.edu-servers.net.
edu.			172800	IN	NS	j.edu-servers.net.
edu.			172800	IN	NS	h.edu-servers.net.
edu.			172800	IN	NS	f.edu-servers.net.
edu.			172800	IN	NS	k.edu-servers.net.
edu.			172800	IN	NS	l.edu-servers.net.
edu.			86400	IN	DS	35663 13 2 A2E1614291831A4746B5AC52B4B345357687271E85353082741F1CF3 D06A4C1D
edu.			86400	IN	RRSIG	DS 8 1 86400 20261014170000 20261001160000 8763 . laNLmCb7C1jvgbGP62R/S+D2lKnDi6B7XooR4kOwVhbu33I8+RyHHvPh 7YSjvDzWBeI307/Mg8PGJQImvITqTKDqM/GKchfL9S0Mrqdaa7TMJyxM qne79NZIghU4Wk6Lu8Y0EzNfZ/nIJ18wFKNYWdsRaM9uAU+4FOVd2fED iabKW7kTqqmsTdTLhOkil9Eveid8n5QIXv8HgRi/P1UUmA8k4/L8UIA/ 3gWxQXNM9MX+W185eAbxaChJtsYnbA1n8rCDlRX/DijYcAnd+EINxrCn hgbx5lBrjbji5JxopwatdSav73XQZrlODoPEYg5JpBO+6iOzDY+EwIjL NBeJyw==
;; Received 1179 bytes from 202.12.27.33#53(m.root-servers.net) in 43 ms

umass.edu.		172800	IN	NS	ns1.umass.edu.
umass.edu.		172800	IN	NS	ns3.umass.edu.
umass.edu.		172800	IN	NS	ns2.umass.edu.
9DHS4EP5G85PF9NUFK06HEK0O48QGK77.edu. 900 IN NSEC3 1 1 0 - 9IRJMUEL398SEJH8CRDIK2H2K85K5243  NS SOA RRSIG DNSKEY NSEC3PARAM
9DHS4EP5G85PF9NUFK06HEK0O48QGK77.edu. 900 IN RRSIG NSEC3 13 2 900 20261007033834 20260930022834 6705 edu. yNjVHMK6hKZ3CAJa5Xo5vCPmb/6vGWApht8wcHO2KOdee68kzPnMQkmU VdN8svVDm71t+KfdH0bFuslg8G38gA==
KSTA9AL56BJ578KRJIHPADGQ1E5T866H.edu. 900 IN NSEC3 1 1 0 - L0VVF1G830DN9CAR2PUL087VSP8EIL6S  NS DS RRSIG
KSTA9AL56BJ578KRJIHPADGQ1E5T866H.edu. 900 IN RRSIG NSEC3 13 2 900 20261007033833 20260930022833 6705 edu. xqtIkn5lwisjAQwrH7Zo4AwAAigENd89D9KDoNV2hdC8bIfCZvH2sOXf Z4bwsNSnPY5iLorJ2FNOvB04Xz1Obg==
;; Received 505 bytes from 192.43.172.30#53(i.edu-servers.net) in 41 ms

gaia.cs.umass.edu.	3600	IN	A	128.119.245.12
;; Received 62 bytes from 128.119.10.28#53(ns2.umass.edu) in 123 ms
```
Read the output in blocks. Each block ends with a line `;; Received ... from <server>` that says who answered: first a root server (which points to the `.edu` servers), then a `.edu` server (which points to the `umass.edu` servers), then a `umass.edu` server, which finally gives the address.
