# TCP congestion control: NewReno vs Cubic

Kurose & Ross, Ch. 3: Sec. 3.7 (TCP congestion control, TCP CUBIC).

A client sends as fast as it can to a server on your own machine (loopback). An emulator in the middle is a **bottleneck**: a slow link with a short queue. When the queue is full a packet is dropped and TCP reduces its congestion window `cwnd`. The client reads `cwnd` from its own kernel and saves it in a CSV file.

![Emulated channel](img/channel.svg)

- **Data**: router queue (50 packets), then the link (10 Mbit/s). This is the queue of the textbook: it fills up and drops packets.
- **ACKs**: the same router queue and link (a real link has both directions), then the cable (100 ms). ACKs are small (66 bytes against 1066, Ethernet header included): their queue stays almost always empty.
- The cable holds every packet in flight: in the emulator we give it room for ≈ 1500 packets, in practice unlimited.

RTT ≈ 100 ms.

| File | What it does |
|---|---|
| `emulate_channel.sh` | **the channel** (Linux): link speed, delay, loss, queue; `start`, `show`, `stop` |
| `tcp_server.py` | receives everything on port 12000, from many clients at the same time |
| `cwnd_client.py` | sends for `--time` seconds; every `--every` seconds prints and saves `time,cwnd,ssthresh,rtt,bytes` |
| `plot_cwnd.py` | draws the `cwnd` of one or more CSV files in `--out` (default `cwnd.png`; also `.svg`, `.pdf`), on the real (absolute) time |
| `plot_rtt.py` | draws the **RTT** (ms) of one or more CSV files in `--out` (default `rtt.png`), on the real time; `--delay 100` also draws the cable delay |
| `plot_thr.py` | draws the **throughput** (Mbit/s) of one or more CSV files in `--out` (default `thr.png`), on the real (absolute) time; `--link 10` also draws the link capacity (Mbit/s) |

| Option | What it does (default) |
|---|---|
| `--cc` | algorithm, `reno`, `cubic` or `bbr` (cubic) |
| `--time` | seconds of sending (30) |
| `--every` | seconds between two samples (0.05) |
| `--out` | CSV file for the samples (cwnd.csv) |

Output columns: `time` = absolute time ([Unix time](https://docs.python.org/3/library/time.html#time.time): seconds since 1 Jan 1970), `cwnd` and `ssthresh` in segments (MSS = 1000 bytes), `rtt` = smoothed RTT in ms, `bytes` = bytes acked by the server so far. The plot scripts put time 0 at the first sample of all their files: runs made one after the other appear one after the other, clients started together appear together. Before the first loss `ssthresh` is only a placeholder (0 or a big number): ignore it.

---

## Theory

- **Reno**: in congestion avoidance `cwnd` grows by 1 MSS per RTT (a straight line). At a loss (3 duplicate ACKs): `ssthresh = cwnd / 2`, `cwnd = ssthresh`. Result: a **sawtooth**.
- **Cubic**: at a loss `cwnd` goes down only to **0.7 ·** `cwnd`. Then it grows as a cubic function of the time since the loss: fast when far from the old maximum, slow near it (concave), then fast again to look for more bandwidth (convex).

> **Reno or NewReno?** Linux calls it `reno`, but it is NewReno. Same `cwnd` rules as Reno; the only difference is fast recovery when **more than one** segment is lost in the same window: Reno exits at the first new ACK, NewReno stays until all of them are retransmitted.

---

## Setup

Open two terminals: one for the **server**, one for the **client**.

Start `tcp_server.py` in the server terminal. Leave it running for all the exercises.

Start the channel in the client terminal: `./emulate_channel.sh start` (see below).

---

## Emulator (sudo)

The emulator is the **channel** of the experiment: the data packets (to port 12000) get a router queue and a link; the ACKs (from port 12000) get the same queue and link, then a cable that adds the delay.

### `emulate_channel.sh`

One script does everything: **you only choose the channel, then look at the results**.

```bash
./emulate_channel.sh start     # start (or restart) the channel
./emulate_channel.sh show      # show the current settings
./emulate_channel.sh stop      # remove it, at the end
```

| Variable | What it is | Default |
|---|---|---|
| `DELAY` | one-way delay of the cable: RTT ≈ `DELAY` | `100ms` |
| `LOSS` | random loss of the data packets | `0%` |
| `QUEUE` | router queue, in packets | `50` |
| `RATE` | link speed | `10mbit` |

Change a value by writing it before the command; the others keep the default. `start` always removes the old settings first: no need to `stop` between two scenarios.
```bash
./emulate_channel.sh start                         # the channel of exercises 1-3 and 5
LOSS=0.1% ./emulate_channel.sh start               # exercise 4
RATE=1000mbit DELAY=1ms ./emulate_channel.sh start # another scenario: fast link, short cable
```
It asks for the `sudo` password. With `RATE` other than 10 Mbit/s, give the same value to `plot_thr.py --link` (in Mbit/s).

> **Preview.** Here `tc` is only a tool: we will study network emulation in much more detail later in the course.

> <details>
> <summary><b>What the script runs</b> (click to open)</summary>
>
> With the default values:
> ```
> sudo tc qdisc del dev lo root
> sudo ethtool -K lo tso off gso off
> sudo tc qdisc add dev lo root handle 1: prio
> sudo tc qdisc add dev lo parent 1:1 handle 10: netem rate 10mbit limit 50 loss 0%
> sudo tc qdisc add dev lo parent 1:3 handle 30: netem delay 100ms limit 1500
> sudo tc qdisc add dev lo parent 30:1 handle 31: tbf rate 10mbit burst 1540 limit 52000
> sudo tc filter add dev lo parent 1: protocol ip u32 match ip dport 12000 0xffff flowid 1:1
> sudo tc filter add dev lo parent 1: protocol ip u32 match ip sport 12000 0xffff flowid 1:3
> ```
> Data: `netem rate ... limit 50 loss ...` is the link, its router queue (packets) and the random loss. ACKs: `netem delay 100ms limit 1500` is the cable (room for 1500 packets), then `tbf` is the link with its router queue (`limit` in bytes: 52000 ≈ 50 packets). `ethtool` turns off TSO/GSO, so the emulator sees real 1000-byte segments and not 64 KB blocks.
>
> `stop` runs `sudo tc qdisc del dev lo root` and `sudo ethtool -K lo tso on gso on`. Details: [man tc-netem](https://man7.org/linux/man-pages/man8/tc-netem.8.html).
>
> </details>


### Check that it works

Start `cwnd_client.py --time 10` in the client terminal.

- Emulator **working**: `cwnd` stays below ≈ 180 segments and falls down at each loss.
- Emulator **not active**: `cwnd` grows to thousands of segments. Run `./emulate_channel.sh start`.
- `cwnd` always falls around 50 or less: an old loss setting is still there. Check with `./emulate_channel.sh show`, then run `./emulate_channel.sh start` again.

---

## Choose the algorithm

The first line of the client output tells which algorithm is in use, e.g. `congestion control: cubic`.

Per connection, with the `--cc` option of the client. No `sudo`.

How the client does it (only to read the code):
- `setsockopt(TCP_CONGESTION)` chooses the algorithm, `getsockopt(TCP_INFO)` returns `cwnd`, `ssthresh`, RTT and acked bytes ([man tcp](https://man7.org/linux/man-pages/man7/tcp.7.html)).
- `struct.unpack_from("I", info, 80)` reads the 4-byte number at byte 80 of the kernel answer ([Python struct](https://docs.python.org/3/library/struct.html)).


---

## 1. Cubic

**Step 1.** Choose **Cubic** (`--cc cubic`).

**Step 2.** Start `cwnd_client.py --cc cubic --time 40 --out cubic.csv` in the client terminal.

**Step 3.** Watch `cwnd` and `ssthresh` while it runs.

Example (real run, macOS):
```
time,cwnd,ssthresh
1793869173.520,172,95
1793869173.560,174,95
1793869173.610,122,122
1793869173.670,122,122
...
1793869179.360,143,119
1793869179.410,144,119
```

What to find in your output:
- At each loss, `ssthresh` ≈ **0.7 ·** the `cwnd` just before it.
- After a loss `cwnd` grows fast, becomes flat near (a bit below) the old maximum, then speeds up again.

---

## 2. NewReno

**Step 1.** Choose **NewReno** (`--cc reno`).

**Step 2.** Start `cwnd_client.py --cc reno --time 40 --out reno.csv` in the client terminal.

Example (real run, macOS):
```
time,cwnd,ssthresh
1793868550.320,169,90
1793868550.370,169,90
1793868550.410,85,85
1793868550.470,85,85
...
1793868550.820,86,85
1793868550.860,43,43
```

What to find in your output:
- At each loss, `ssthresh` ≈ **half** of the `cwnd` just before it.
- Sometimes a second loss comes a few RTTs later: `cwnd` halves again (here 169 → 85 → 43).
- After a loss `cwnd` grows by ≈ 1 every RTT: with one sample every 0.05 s, +1 every 2–3 lines (the queue adds up to 40 ms to the RTT).

---

## 3. Compare

Start `plot_cwnd.py reno.csv cubic.csv` in the client terminal and open `cwnd.png`.

![NewReno vs Cubic, real run on macOS](img/reno_vs_cubic.svg)

What to find in the plot:
- NewReno: a regular **sawtooth**, deep teeth (down to half), straight rising lines.
- Cubic: shallow teeth (down to 0.7), curved rising lines, flat near (a bit below) the old maximum.
- Cubic keeps a **larger `cwnd` on average** (here 131 segments against 103).
- The link is full with ≈ 120 segments in flight (10 Mbit/s × 100 ms): Cubic falls back to about that value, NewReno goes well below it and leaves the link partly empty for many seconds.

Now look at what the user gets: the **throughput**. Start `plot_thr.py reno.csv cubic.csv --link 10` and open `thr.png` (`--link` = the link speed of the emulator, in Mbit/s). It also prints the average throughput of each run.

What to find in the plot:
- The throughput never goes above ≈ 9.38 Mbit/s: it counts only the data, while the link carries whole packets. Each packet has 1000 bytes of data in 1066 (TCP 20 + Timestamps 12 + IP 20 + Ethernet 14): 10 × 1000 / 1066 = 9.38. This is the **goodput**: with the headers the link is 100 % full.
- Throughput ≈ `cwnd · MSS / RTT`, but only up to the link: with more than ≈ 120 segments in flight the extra ones wait in the queue (the `rtt` column grows) and the throughput stays flat.
- After a loss the throughput goes down only if `cwnd` falls below ≈ 120: NewReno (down to half) loses throughput for a few seconds, Cubic (down to 0.7) almost never.

---

## 4. Random loss

Until now every loss came from the full queue: a **congestion** loss. Now we add losses that have nothing to do with congestion (e.g. a noisy radio link): TCP cannot tell the difference.

**Step 1.** Activate 0.1 % loss: `LOSS=0.1% ./emulate_channel.sh start`.

**Step 2.** Repeat exercises 1 and 2 with `--out cubic_loss.csv` and `--out reno_loss.csv`.

**Step 3.** Start `plot_cwnd.py reno_loss.csv cubic_loss.csv --out cwnd_loss.png` and open `cwnd_loss.png`.

<!-- TODO: example plot from a real run -->

What to find in the plot:
- Losses come at **random** `cwnd` values, well below 170: the queue is no longer the reason.
- Both stay below the ≈ 120 segments needed to fill the link: part of the link is wasted.
- Cubic suffers less: it falls only to 0.7 and climbs back faster.

**Step 4.** Remove the random loss: `./emulate_channel.sh start`.

---

## 5. Together (optional)

Until now each algorithm had the bottleneck all for itself. Two connections can also **share** it at the same time: the server reads many clients at once.

**Step 1.** In two client terminals, start one NewReno and one Cubic client a few seconds apart, with `--out reno_mix.csv` and `--out cubic_mix.csv`.
- `--cc reno` in one, `--cc cubic` in the other.

**Step 2.** Start `plot_cwnd.py reno_mix.csv cubic_mix.csv --out mix.png`, then `plot_thr.py reno_mix.csv cubic_mix.csv --link 10 --out mix_thr.png`. Both clients write absolute time: in the plot the two curves line up, even if one client started a few seconds later.

Real run (Linux, default channel): NewReno alone for 20 s, then Cubic joins, then Cubic alone.

![cwnd, NewReno and Cubic sharing the link](img/mix_cwnd.svg)

![throughput, NewReno and Cubic sharing the link](img/mix_thr.svg)

What to find in the plots:
- Alone, each flow fills the link (≈ 9.38 Mbit/s).
- Together the sum stays ≈ 9.38 Mbit/s: the link is still full, but shared.
- The share is not fair: NewReno halves at each loss and grows by 1 per RTT, Cubic falls only to 0.7 and climbs back faster. Here, from 20 to 40 s, Cubic got ≈ 5.4 Mbit/s and NewReno ≈ 4.0, and at the end ≈ 7 against 2.5.

The two flows now compete for the same queue: how they share the link is the topic of **TCP fairness** (Kurose Sec. 3.7.2).

---

## 6. BBR

Reno and Cubic are **reactive**: they grow until the queue is full and a packet is lost, then back off. BBR (Google, 2016) uses no alarm signal: it **measures** the path, the bottleneck bandwidth (the highest delivery rate it sees) and the propagation RTT (the lowest RTT it sees), and sends at that rate with about `bandwidth × RTT` bytes in flight. Ideally the link is full and the queue stays empty.

How BBR moves in time:
- **Startup**: doubles the rate every RTT (like slow start) until the delivery rate stops growing, then **Drain** empties the queue it has made.
- **ProbeBW** (most of the time): a cycle of 8 RTTs, 1 at 1.25 × the rate (is there more bandwidth?), 1 at 0.75 (empty what the probe queued), 6 at 1.
- **ProbeRTT**: if in 10 s the RTT never went down to its minimum, `cwnd` drops to 4 segments for ≈ 200 ms, to empty the queue and measure the real propagation RTT.

The kernel has BBR v1; `./emulate_channel.sh start` loads it.

**Step 1.** Start the default channel: `./emulate_channel.sh start`.

**Step 2.** Run Cubic, then BBR, one after the other:
```bash
python cwnd_client.py --cc cubic --time 40 --out cubic.csv
python cwnd_client.py --cc bbr   --time 40 --out bbr.csv
```

**Step 3.** Plot the three quantities:
```bash
python plot_cwnd.py cubic.csv bbr.csv --out bbr_cwnd.png
python plot_thr.py cubic.csv bbr.csv --link 10 --out bbr_thr.png
python plot_rtt.py cubic.csv bbr.csv --delay 100 --out bbr_rtt.png
```

What to find:
- **Throughput**: both reach ≈ 9.38 Mbit/s, the full link. BBR gets there with no loss.
- **RTT**: Cubic stays well above the 100 ms of the cable, because it keeps the queue full. BBR stays close to 100 ms: the queue is almost empty. Same throughput, much less delay.
- **`cwnd`**: no sawtooth for BBR. It stays near the ≈ 120 segments of `bandwidth × RTT`, and every ≈ 10 s it drops for a moment to 4 (**ProbeRTT**).

**Step 4: random loss.** Start `LOSS=1% ./emulate_channel.sh start` and repeat steps 2 and 3 with `--out cubic_loss1.csv` and `--out bbr_loss1.csv`.

What to find:
- Cubic reads every lost packet as congestion: its `cwnd` stays small and the throughput falls to a small part of the link.
- BBR does not use loss as a signal: it keeps sending at the rate it measured, and the throughput stays close to the link.

**Step 5: together (optional).** Cubic and BBR start **at the same moment** on the same router queue. Who gets more of the link depends on the size of the queue Q compared with the BDP (≈ 117 packets here).

![model: BBR and Cubic on the same queue](img/bbr_cubic_model.svg)

The model, in three lines:
- the network holds **BDP + Q** packets (cable + queue), and each flow gets a share of the link equal to its share of these packets;
- **BBR** keeps at most **2 BDP** in flight: its `cwnd` is 2 × the BDP it measures (the factor 2 is a margin for late ACKs). It does not grow at the losses;
- **Cubic** grows until the queue overflows: it takes all the rest, **Q − BDP**.

So **BDP + Q = BBR + Cubic = 2 BDP + (Q − BDP)**, and the two get the same share when Q − BDP = 2 BDP, that is **Q = 3 BDP**. Smaller queue: BBR wins. Larger queue: Cubic wins.

| queue | `QUEUE` | compared with the BDP | expected |
|---|---|---|---|
| small | 50 | ≈ 0.4 BDP | BBR wins |
| medium | 350 | ≈ 3 BDP | half each |
| large | 1000 | ≈ 8.5 BDP | Cubic wins |

For each queue, set `QUEUE` in the first line and run (180 s: see the transient below):
```bash
QUEUE=350

QUEUE=$QUEUE ./emulate_channel.sh start

python cwnd_client.py --cc cubic --time 180 --out q${QUEUE}_cubic.csv > /dev/null &
python cwnd_client.py --cc bbr   --time 180 --out q${QUEUE}_bbr.csv   > /dev/null
wait

python plot_thr.py  q${QUEUE}_cubic.csv q${QUEUE}_bbr.csv --link 10 --out q${QUEUE}_thr.png
python plot_cwnd.py q${QUEUE}_cubic.csv q${QUEUE}_bbr.csv           --out q${QUEUE}_cwnd.png
```
`&` starts Cubic in the background, so the two clients start together; `wait` waits for it. Write `${QUEUE}` with braces (`$QUEUE_cubic` would be a variable named `QUEUE_cubic`). Start a run only when the previous one is over.

Real run, **small queue** (50 packets): BBR ≈ 7.6 Mbit/s, Cubic ≈ 1.5. The network holds BDP + 50 ≈ 167 packets, less than the ≈ 230 BBR wants: the queue overflows all the time, and only Cubic backs off. The `cwnd` of BBR stays flat at ≈ 230 = 2 BDP; every ≈ 10 s it drops to 4 for ≈ 200 ms (**ProbeRTT**, to measure the RTT of the empty cable).

![throughput, Cubic and BBR, queue 50](img/q50_thr.svg)

Real run, **medium queue** (350 packets ≈ 3 BDP), 180 s:

![throughput, Cubic and BBR, queue 350](img/q350_thr.svg)

| | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s | 60-180 s (steady state) |
|---|---|---|---|---|---|---|
| share of BBR | 18 % | 16 % | 23 % | 37 % | 39 % | **47 %** (every 10 s: between 38 and 54 %) |

- **Transient** (first ≈ 50 s): Cubic starts strong, BBR grows slowly. BBR raises its estimate of the bandwidth only in 1 RTT out of 8, and with the queue full the RTT is ≈ 0.57 s.
- **Steady state**: ≈ half each, as the model says. Not a flat line: the share moves by a few %, at each ProbeRTT of BBR (the dips to 0).

> **Beware of the transient.** Stop this run at 30 s and you read "Cubic takes ≈ 80 %, the model is wrong"; at 180 s it is ≈ half each. Nothing changed in the network, only **when** we looked. Plot the throughput over time, and average only where it has stopped moving.

**Step 6.** Back to the default channel: `./emulate_channel.sh start`.

---

## References

For the curious, to study the details:
- [RFC 5681](https://www.rfc-editor.org/rfc/rfc5681): TCP congestion control (Reno)
- [RFC 6582](https://www.rfc-editor.org/rfc/rfc6582): NewReno
- [RFC 9438](https://www.rfc-editor.org/rfc/rfc9438): CUBIC
- [BBR: Congestion-Based Congestion Control](https://queue.acm.org/detail.cfm?id=3022184), Cardwell et al., ACM Queue 2016
