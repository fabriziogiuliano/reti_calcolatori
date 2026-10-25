# TCP SACK and Timestamps

Kurose & Ross, Ch. 3: Sec. 3.4.3 (GBN, SR), Sec. 3.5.3 (RTT, timeout).

A client sends a stream to a server on your own machine (loopback). An emulator in the middle loses data packets and delays ACKs. A Scapy sniffer prints the TCP header of every packet.

![Emulated channel](img/channel.svg)

The sniffer sees each packet when it comes out of the channel: lost packets never reach it. Data has no delay, so RTT = ACK delay.

| File | What it does |
|---|---|
| `tcp_server.py` | receives everything on port 12000 |
| `tcp_client.py` | sends `--n` chunks of `--size` bytes (default 1000), one every `--interval` seconds |
| `01_sack_sniffer.py` | one line per packet: flags, `seq`, `ack`, `win`, length, SACK blocks |
| `02_01_ts_sniffer.py` | one line per packet: flags, `seq`, `ack`, length, `TSval`, `TSecr` |
| `02_02_rto_sniffer.py` | the same as `02_01`, plus the `RTO` column |

---

## Setup

Open three terminals (windows, tabs or tmux panes: as you like): one for the **server**, one for the **sniffer**, one for the **client**.

Start `tcp_server.py` in the server terminal. Leave it running for all the exercises.

On Linux the sniffers need root: start them with `sudo $(which python)` instead of `python`.

---

## Emulator (sudo)

The emulator makes data packets (to port 12000) lossy and ACKs (from port 12000) slow. All its commands need `sudo`.

> **Preview.** Here `tc` (Linux) and `dnctl` (macOS) are only a tool: copy the commands as they are. We will study network emulation in much more detail later in the course.

Read **only the part for your system**.

### Linux / WSL

**Start** (once). All values start at 0: no loss, no delay.
```
sudo ethtool -K lo tso off gso off
sudo tc qdisc add dev lo root handle 1: prio
sudo tc qdisc add dev lo parent 1:1 handle 10: netem loss 0%
sudo tc qdisc add dev lo parent 1:3 handle 30: netem delay 0ms
sudo tc filter add dev lo parent 1: protocol ip u32 match ip dport 12000 0xffff flowid 1:1
sudo tc filter add dev lo parent 1: protocol ip u32 match ip sport 12000 0xffff flowid 1:3
```

**Change** loss and delay (here: data loss 20 %, ACK delay 100 ms). Each exercise tells you the values.
```
sudo tc qdisc change dev lo parent 1:1 handle 10: netem loss 20%
sudo tc qdisc change dev lo parent 1:3 handle 30: netem delay 100ms
```
The first line sets the data loss, the second one the ACK delay.

**Stop** (at the end).
```
sudo tc qdisc del dev lo root
sudo ethtool -K lo tso on gso on
```
Details: [man tc](https://man7.org/linux/man-pages/man8/tc.8.html).

### macOS

**Start** (once). All values start at 0: no loss, no delay.
```
sudo dnctl pipe 1 config plr 0
sudo dnctl pipe 2 config delay 0
printf "dummynet out on lo0 proto tcp from any to any port 12000 pipe 1\ndummynet out on lo0 proto tcp from any port 12000 to any pipe 2\n" | sudo pfctl -f -
sudo pfctl -e
```
`pfctl` prints some warnings (`flushing of rules`, `No ALTQ`): they are normal.

**Change** loss and delay (here: data loss 20 %, ACK delay 100 ms). Each exercise tells you the values.
```
sudo dnctl pipe 1 config plr 0.2
sudo dnctl pipe 2 config delay 100
```
The first line sets the data loss (`plr` = packet loss rate, from 0 to 1), the second one the ACK delay (ms).

**Stop** (at the end).
```
sudo pfctl -f /etc/pf.conf
sudo pfctl -d
sudo dnctl -q flush
```
Details: [man dnctl](https://keith.github.io/xcode-man-pages/dnctl.8.html).

### Check that it works

Do not skip this check: if the emulator is off, nothing in the exercises will make sense.

1. With the **Change** commands of your system, set an ACK delay of **500 ms** (loss 0).
2. Start `tcp_client.py --n 10 --interval 0` in the client terminal.

**Client output** (emulator working)
```
MSS: 1000 bytes
handed 10 chunks of 1000 bytes to TCP in 0.00 s
all data delivered after 0.50 s
```
The second time must be **about 0.5 s larger** than the first one: the ACKs wait 500 ms in the emulator.

If both times are `0.00 s`, the emulator is **not** active: run the **Start** commands again and repeat the check. On macOS this happens after every reboot, and after the **Stop** commands.

3. When it works, set the ACK delay back to **0**.

---

## 1. SACK

**Step 1.** With the **Change** commands of your system, set: data loss **20 %**, ACK delay **0**.

**Step 2.** Start `01_sack_sniffer.py` in the sniffer terminal.

**Step 3.** Start `tcp_client.py --n 10 --interval 0.1` in the client terminal.

**Step 4.** Read the sniffer output. Losses are random: every run is different.

Each field of a line:
- `ts`: ms since the start of the connection
- `S`, `A`, `F`: flags SYN, ACK, FIN
- `seq`, `ack`: relative numbers (the first data byte is 1)
- `win`: receive window of the sender of the packet, in bytes
- `SACK,SLE:x,SRE:y`: the receiver **has** bytes x … y-1 (out of order)

Example (real run, Linux):
```
ts:00207,SPORT:47846,DPORT:12000,S:0,A:1,F:0,seq:02001,ack:00001,win:0064768,data_len:1000
ts:00207,SPORT:12000,DPORT:47846,S:0,A:1,F:0,seq:00001,ack:03001,win:0065664,data_len:0
ts:00414,SPORT:47846,DPORT:12000,S:0,A:1,F:0,seq:04001,ack:00001,win:0064768,data_len:1000
ts:00414,SPORT:12000,DPORT:47846,S:0,A:1,F:0,seq:00001,ack:03001,win:0065664,data_len:0,SACK,SLE:04001,SRE:05001
ts:00414,SPORT:47846,DPORT:12000,S:0,A:1,F:0,seq:03001,ack:00001,win:0064768,data_len:1000
ts:00414,SPORT:12000,DPORT:47846,S:0,A:1,F:0,seq:00001,ack:05001,win:0064640,data_len:0
```

What to find in your output:
- A **missing** segment: here `seq:03001` never appears after `seq:02001` (the emulator dropped it).
- An ACK with SACK: `ack:03001` = first missing byte, `SLE:04001,SRE:05001` = what arrived after the hole. The receiver has 1-3000, **misses 3001-4000**, has 4001-5000.
- The sender sends again **only the missing segment** `seq:03001` (as in SR, not GBN).
- After the hole is filled, `ack` **jumps** to 5001.

---

## 2. Timestamps

**Step 1.** With the **Change** commands of your system, set: data loss **0**, ACK delay **100 ms**.

**Step 2.** Stop the sniffer (Ctrl+C) and start `02_01_ts_sniffer.py` in the sniffer terminal.

**Step 3.** Start `tcp_client.py --n 10 --interval 0.1` in the client terminal.

**Step 4.** Read the two new fields:
- `TSval`: clock of the sender when it sent the packet (ms)
- `TSecr`: the `TSval` of the other side, copied back

Example (real run, macOS):
```
ts:121.05,SPORT:59671,DPORT:12000,S:0,A:1,F:0,seq:01001,ack:00001,data_len:1000,TSval:00121,TSecr:00019
ts:221.31,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:02001,data_len:0,TSval:00121,TSecr:00121
ts:222.74,SPORT:59671,DPORT:12000,S:0,A:1,F:0,seq:02001,ack:00001,data_len:1000,TSval:00223,TSecr:00121
ts:323.58,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:03001,data_len:0,TSval:00223,TSecr:00223
```

What to find in your output:
- The data segment `seq:01001` leaves with `TSval:00121`.
- Its ACK (`ack:02001`) carries `TSecr:00121`: the same number, copied back.
- Between the two lines `ts` grows by ≈ 100 ms (121 → 221): that is the RTT the sender measures, `SampleRTT = now - TSecr`.

---

## 3. RTO

**Step 1.** Keep the emulator as in exercise 2 (ACK delay 100 ms).

**Step 2.** Stop the sniffer (Ctrl+C) and start `02_02_rto_sniffer.py` in the sniffer terminal.

**Step 3.** Start `tcp_client.py --n 20 --interval 0.1` in the client terminal.

**Step 4.** Look at the last column, `RTO` (ms). It is computed from each `SampleRTT` with Jacobson's formulas (Kurose Sec. 3.5.3):
```
EstimatedRTT    = 7/8 · EstimatedRTT + 1/8 · SampleRTT
DevRTT          = 3/4 · DevRTT + 1/4 · |SampleRTT - EstimatedRTT|
TimeoutInterval = EstimatedRTT + 4 · DevRTT
```

Example (real run, macOS, only the ACK lines):
```
ts:119.44,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:01001,data_len:0,TSval:00019,TSecr:00019,RTO:00301.3
ts:221.31,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:02001,data_len:0,TSval:00121,TSecr:00121,RTO:00251.2
ts:323.58,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:03001,data_len:0,TSval:00223,TSecr:00223,RTO:00213.9
ts:428.57,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:04001,data_len:0,TSval:00328,TSecr:00328,RTO:00185.6
...
ts:2086.63,SPORT:12000,DPORT:59671,S:0,A:1,F:0,seq:00001,ack:20001,data_len:0,TSval:01987,TSecr:01987,RTO:00103.7
```

What to find in your output:
- Before the first ACK, `RTO` = 1000 (1 s, the starting value).
- At each ACK the `RTO` goes down: 301, 251, 214, 186 … until ≈ 104 ms, close to the real RTT (100 ms).

**Step 5.** Start the client again with `--n 100 --interval 0.1`. While it is sending, raise the ACK delay to **300 ms** (Change commands of your system). The `RTO` goes up quickly, then settles close to 300 ms.

---

## References

For the curious, to study the details:
- [RFC 2018](https://www.rfc-editor.org/rfc/rfc2018): the SACK option
- [RFC 7323](https://www.rfc-editor.org/rfc/rfc7323): the Timestamps and Window Scale options
- [RFC 6298](https://www.rfc-editor.org/rfc/rfc6298): how TCP computes the RTO
- [Scapy, sniffing](https://scapy.readthedocs.io/en/latest/usage.html#sniffing): the `sniff()` function used by the sniffers
