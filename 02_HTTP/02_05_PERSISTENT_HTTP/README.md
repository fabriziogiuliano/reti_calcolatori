# 02.5 Persistent vs non-persistent HTTP

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.2.2)

## Concepts

1. **Non-persistent** HTTP: a **new TCP connection for every object**. Every object costs **2 RTT**: 1 for the TCP handshake, 1 for the HTTP request and response.
2. **Persistent** HTTP: **one TCP connection for many objects**. The first object costs 2 RTT, every next object only **1 RTT**: the connection is already open.
3. HTTP/1.0 is non-persistent by default, HTTP/1.1 is persistent by default.

| N objects | Non-persistent | Persistent |
|---|---|---|
| time | N × 2 RTT | 2 RTT + (N − 1) × 1 RTT |

## Files

| File | What it is |
|---|---|
| `server.py` | A web server, port **8000**. It logs every TCP connection (`OPEN` / `CLOSED`) and every request on it, with the **client port**: same port = same TCP connection |

In `server.py` two lines matter:
```python
RTT = 0.5                          # seconds: our (artificial) round-trip time
protocol_version = 'HTTP/1.1'      # the server can do both: the CLIENT decides (curl --http1.0 / --http1.1)
```
On localhost the real RTT is almost zero, so the server **adds it by itself** with `time.sleep`: 1 RTT for every new connection (the handshake) and 1 RTT for every request.

**We never change the server.** We change only the client: `curl --http1.0` (non-persistent) or `curl --http1.1` (persistent).

Use two tmux panes: the **server** on the left, the **client commands** on the right. Start `server.py` in the left pane. It prints:
```
22:03:43.120  Server on http://localhost:8000 (HTTP/1.1, RTT 0.5 s)
```

---

## Part A. Non-persistent (HTTP/1.0)

### Step 1. Predict

We will download **3 objects** with RTT = 0.5 s and **HTTP/1.0**. How long will each one take? And all together? Write it down.

### Step 2. Measure

**What it does:** `[1-3]` makes curl ask for `/1`, `/2`, `/3`: **3 objects, one after the other**, with one command. `--http1.0` uses HTTP/1.0. `-s` (silent) hides the progress bar. `-w` prints the time of each one.

> **`-w` (write-out):** after every download, curl prints the text you give it. The parts written as `%{...}` are **curl variables**: curl fills them in by itself. `%{time_total}` = how many seconds that download took. Online: [Write out - everything curl](https://everything.curl.dev/usingcurl/verbose/writeout.html) (a friendly guide with examples) and the [full list of variables](https://curl.se/docs/manpage.html#--write-out) in the official manual (or `man curl` in the terminal).

```bash
curl --http1.0 -s -w 'time: %{time_total}s\n' 'http://localhost:8000/[1-3]'
```
**Client output**
```
You asked for /1
time: 1.012539s
You asked for /2
time: 1.011516s
You asked for /3
time: 1.011871s
```
**Server log:**
```
22:03:43.551  [port 58910] connection OPEN
22:03:44.562  [port 58910]   GET /1 HTTP/1.0
22:03:44.564  [port 58910] connection CLOSED after 1 request(s)
22:03:44.566  [port 58912] connection OPEN
22:03:45.574  [port 58912]   GET /2 HTTP/1.0
22:03:45.574  [port 58912] connection CLOSED after 1 request(s)
22:03:45.575  [port 58914] connection OPEN
22:03:46.582  [port 58914]   GET /3 HTTP/1.0
22:03:46.583  [port 58914] connection CLOSED after 1 request(s)
```
**3 connections, 1 request each** (3 different ports). Every object costs 2 RTT = 1 s. Total: **3 s**.

The server could keep the connection open, but the client speaks HTTP/1.0: the server closes the connection after every answer.

---

## Part B. Persistent (HTTP/1.1)

### Step 3. Predict, then measure

Same 3 objects, now with **HTTP/1.1**. How long for each object and in total? Write it down, then run:

```bash
curl --http1.1 -s -w 'time: %{time_total}s\n' 'http://localhost:8000/[1-3]'
```
**Client output**
```
You asked for /1
time: 1.011370s
You asked for /2
time: 0.506129s
You asked for /3
time: 0.506059s
```
**Server log:**
```
22:03:46.608  [port 58916] connection OPEN
22:03:47.615  [port 58916]   GET /1 HTTP/1.1
22:03:48.117  [port 58916]   GET /2 HTTP/1.1
22:03:48.623  [port 58916]   GET /3 HTTP/1.1
22:03:48.624  [port 58916] connection CLOSED after 3 request(s)
```
**1 connection, 3 requests** (always port 58916). Look at the times: 1 s from `OPEN` to the first `GET`, then only 0.5 s between one `GET` and the next. The first object costs 2 RTT = 1 s, the others 1 RTT = 0.5 s. Total: **2 s**.

### Step 4. curl says it too

**What it does:** `-v` (verbose) shows what curl does with the connection. `-v` writes on the error channel (stderr): `2>&1` sends it to the normal output, so that `grep` can keep only the lines we want.

```bash
curl --http1.0 -sv 'http://localhost:8000/[1-2]' 2>&1 | grep -iE 're-using|closing'
curl --http1.1 -sv 'http://localhost:8000/[1-2]' 2>&1 | grep -iE 're-using|closing'
```
**Client output**
```
* Closing connection
* Re-using existing connection with host localhost
```
HTTP/1.0: the connection is closed. HTTP/1.1: it is reused.

---

## Part C. A real site

No local server here: we ask Google for its small icon **N times**, with **one** curl command. As in Parts A and B, we change only the HTTP version of the client.

| Option | What it does |
|---|---|
| `"...favicon.ico?[1-$N]"` | curl asks `favicon.ico?1`, `favicon.ico?2`, ... up to `favicon.ico?N`: **N requests** |
| `--http1.1` | use HTTP/1.1: **persistent** |
| `--http1.0` | use HTTP/1.0: **non-persistent** |
| `-o /dev/null` | throw away the icons |
| `%{local_port}` | curl variable: the client port: same port = same connection |
| `%{num_connects}` | curl variable: `1` = curl opened a new connection, `0` = it reused the old one |
| `/usr/bin/time -p` | measures the whole command: `real` = **total time** of the N requests |

### Step 5. Persistent (HTTP/1.1)

```bash
N=10; /usr/bin/time -p curl --http1.1 -s -o /dev/null -w 'port %{local_port}  new conn: %{num_connects}  time: %{time_total}s\n' "https://www.google.com/favicon.ico?[1-$N]"
```
**Client output**
```
port 56024  new conn: 1  time: 0.106883s
port 56024  new conn: 0  time: 0.027277s
port 56024  new conn: 0  time: 0.039555s
port 56024  new conn: 0  time: 0.028750s
port 56024  new conn: 0  time: 0.028968s
port 56024  new conn: 0  time: 0.026432s
port 56024  new conn: 0  time: 0.026600s
port 56024  new conn: 0  time: 0.027876s
port 56024  new conn: 0  time: 0.026398s
port 56024  new conn: 0  time: 0.027873s
real 0.38
user 0.01
sys 0.01
```
One connection: the first icon pays the connection, the others do not. **Total: 0.38 s.**

### Step 6. Non-persistent (HTTP/1.0)

The same command with `--http1.0`:
```bash
N=10; /usr/bin/time -p curl --http1.0 -s -o /dev/null -w 'port %{local_port}  new conn: %{num_connects}  time: %{time_total}s\n' "https://www.google.com/favicon.ico?[1-$N]"
```
**Client output**
```
port 56002  new conn: 1  time: 0.149054s
port 56003  new conn: 1  time: 0.098401s
port 56004  new conn: 1  time: 0.098284s
port 56005  new conn: 1  time: 0.110409s
port 56006  new conn: 1  time: 0.102480s
port 56007  new conn: 1  time: 0.102099s
port 56008  new conn: 1  time: 0.101405s
port 56009  new conn: 1  time: 0.100661s
port 56010  new conn: 1  time: 0.141415s
port 56011  new conn: 1  time: 0.099617s
real 1.13
user 0.11
sys 0.02
```
A new connection for every icon. **Total: 1.13 s, clearly more** (in our tests from 1.5 to 3 times more, depending on the network). With https a new connection costs even more than 1 RTT: after the TCP handshake there is also the TLS handshake.

On a real network the times change a little at every run: run both commands two or three times. What never changes is the `port` column.

---

## Questions

**Q1.** With RTT = 0.5 s, how long do **10 objects** take, non-persistent and persistent? Compute first, then check: use `[1-10]`.
```bash
curl --http1.0 -s -w 'time: %{time_total}s\n' 'http://localhost:8000/[1-10]'
curl --http1.1 -s -w 'time: %{time_total}s\n' 'http://localhost:8000/[1-10]'
```

**Q2.** Why does the first object always cost 2 RTT, even with HTTP/1.1?

**Q3.** A web page has 1 HTML file and 10 images. RTT = 100 ms, ignore transmission times. How long does it take to get the whole page, non-persistent and persistent?

**Q4.** Now the opposite: set `protocol_version = 'HTTP/1.0'` in `server.py`, restart it and use `curl --http1.1`. Is the connection persistent? Why?

---

## Solutions

<details>
<summary>Q1</summary>

Non-persistent: 10 × 2 × 0.5 = **10 s** (1 s per object). Persistent: 2 × 0.5 + 9 × 0.5 = **5.5 s** (1 s for the first, 0.5 s for each other).
</details>

<details>
<summary>Q2</summary>

Before the first request there is no connection yet: the TCP handshake (1 RTT) must happen first. Persistent connections save the handshake only for the **next** objects.
</details>

<details>
<summary>Q3</summary>

11 objects. Non-persistent: 11 × 2 × 100 ms = **2.2 s**. Persistent: 2 × 100 ms + 10 × 100 ms = **1.2 s**.
</details>

<details>
<summary>Q4</summary>

**No**: every object takes 1 s and the server logs `connection CLOSED after 1 request(s)` every time. A persistent connection needs **both** sides: if the server speaks HTTP/1.0, it closes the connection after every answer, even if the client would like to keep it open.
</details>
