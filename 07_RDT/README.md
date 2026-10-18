# RDT 3.0 on top of UDP: stop-and-wait

Reference: Kurose & Ross, *Computer Networking*, Ch. 3 (Sec. 3.4.1, 3.4.2)

RDT 3.0 runs at application level: its header travels inside the UDP payload.

| Field | Size |
|---|---|
| `seq` | 1 byte (0, 1, 0, 1, ...) |
| `checksum` | 2 bytes (sum of the bytes) |
| data | `--size` bytes (none in an ACK) |

| Function | What it does |
|---|---|
| `sock.settimeout(t)` | `recvfrom()` raises `socket.timeout` after `t` seconds: the RDT timer |
| `random.random()` | random number in [0, 1): below `--loss` the packet is lost, below `--corrupt` one bit is flipped |
| `x ^ 1` | XOR: flips the last bit of the byte `x` |
| `logging.info(...)` | print a log line; `%(relativeCreated)` adds the ms since the script started |
| `time.perf_counter()` | high-resolution clock: `wait()` checks it in a loop, more precise than `time.sleep()` |

| Option | Script | What it does (default) |
|---|---|---|
| `--rtt` | receiver | round-trip time in seconds, waited before each ACK (0.1) |
| `--loss` | receiver | probability of losing a packet (0) |
| `--corrupt` | receiver | probability of flipping one bit (0) |
| `--n` | sender | packets to send (10) |
| `--size` | sender | data bytes per packet (1000) |
| `--timeout` | sender | seconds before a retransmission (0.5) |
| `--c` | both | link capacity in bit/s (1e9) |
| `--verbose` | both | also log the FSM states |

Without options a script prints its help.

Online: [Python socket](https://docs.python.org/3/library/socket.html), [Python random](https://docs.python.org/3/library/random.html), [Python time](https://docs.python.org/3/library/time.html).

---

## Theory

```
U = (L/C) / (RTT + L/C)
```

`L` = 1000B + 3B header = 8024 bits, `C` = 1 Gbit/s, `RTT` = 100 ms → `L/C` ≈ 0.008 ms → `U` = **0.008 %**

Emulated times:
- `L/C`: before each send, sender and receiver wait `len(pkt) × 8 / --c` seconds
- `RTT`: the receiver waits `--rtt` seconds before each ACK

---

## 1. Measure stop-and-wait

Start `rdt_receiver.py --rtt 0.1 --verbose` in the left pane, then `rdt_sender.py --n 10 --verbose` in the right pane.

With `--verbose` each log line shows the FSM state (as in the Kurose rdt3.0 sender and rdt2.2 receiver) and the ms since the start.

**Sender output**
```
      6.3 ms  [Wait for call 0 from above] send DATA 0
      6.5 ms  [Wait for ACK 0]
    106.8 ms      ACK 0 received
    106.8 ms  [Wait for call 1 from above] send DATA 1
    106.9 ms  [Wait for ACK 1]
...
sent 10 packets of 1000 bytes in 1.00 s
retransmissions: 0
time per packet: 100.234 ms
throughput: 0.08 Mbit/s
utilization of a 1e+09 bit/s link: 0.008 %
```
Same `U` as the theory: the link is idle almost all the time.

---

## 2. Change the RTT

Restart the receiver with another `--rtt`, run the sender again.

| `--rtt` | time per packet | throughput | utilization |
|---|---|---|---|
| `0` | | | |
| `0.01` | | | |
| `0.1` | 100 ms | 0.08 Mbit/s | 0.008 % |

Throughput ≈ L / RTT. The fix is pipelining (Go-Back-N, Selective Repeat).

---

## 3. Lose packets

Restart the receiver with `--rtt 0.1 --loss 0.2 --verbose`, run the sender again with `--verbose`.

**Receiver log**
```
    740.4 ms  [Wait for 0 from below]
    740.5 ms      DATA lost: no ACK
    740.5 ms  [Wait for 0 from below]
   1241.9 ms      DATA 0 received: deliver 1000 bytes
   1341.9 ms      ACK 0 sent
```
**Sender output**
```
    207.1 ms  [Wait for ACK 0]
    708.3 ms      timeout: resend DATA 0
    808.7 ms      ACK 0 received
```
Each loss costs `--timeout` (0.5 s), then the packet is sent again.

---

## 4. Corrupt bits

Restart the receiver with `--rtt 0.1 --corrupt 0.2 --verbose`, run the sender again with `--verbose`.

**Receiver log**
```
      6.9 ms  [Wait for 0 from below]
    530.5 ms      corrupted or duplicate DATA: send the last ACK again
    630.6 ms      ACK 1 sent
    630.6 ms  [Wait for 0 from below]
   1132.1 ms      DATA 0 received: deliver 1000 bytes
```
**Sender output**
```
      6.6 ms  [Wait for ACK 0]
    106.9 ms      wrong ACK: ignore it
    608.0 ms      timeout: resend DATA 0
    708.6 ms      ACK 0 received
```
The checksum detects the flipped bit; the receiver ACKs the previous `seq`. The sender ignores that ACK, waits `--timeout`, sends again.

