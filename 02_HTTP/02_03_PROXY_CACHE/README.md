# 02.3 Web Caching: the Proxy Server

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.2.5)

## Concepts

1. A **proxy server** (web cache) sits in the local network. The browsers are configured to send **all** their requests to it.
2. If the proxy has a copy of the object (**HIT**), it answers by itself. If not (**MISS**), it asks the **origin server**, keeps a copy, then answers.
3. The proxy is **both a server and a client**: a server for the browsers, a client for the origin servers.
4. Why it helps: **shorter response time** and **less traffic** on the access link.
5. With **https** the proxy only passes encrypted bytes: it **cannot cache**.
6. A copy in the cache can become **old**: the proxy does not know that the object changed.

## Files

| File | What it is |
|---|---|
| `origin_server.py` | A web site, port **8000**: serves the files in `www/`. Every answer takes **2 seconds**: an artificial delay (`time.sleep`) that stands for a server far away |
| `proxy_cache.py` | The proxy, port **8080** |
| `www/` | The files of the site: `index.html` and `kiwi.gif` |

```
 LOCAL NETWORK                           FAR AWAY
 [client] ───► [proxy :8080] ──────────► [origin :8000]
```

---

## Part A. Without the proxy

We need three programs. Split the terminal in three with tmux: **origin** in one pane, **proxy** in another, **client commands** in the third.

### Step 1. Start the origin server

Start `origin_server.py` in its pane.

### Step 2. Download the kiwi, twice

**What it does:** `-o /dev/null` throws the body away, `-w` prints the total time.

> **`-w` (write-out):** after the download, curl prints the text you give it. The parts written as `%{...}` are **curl variables**: curl fills them in by itself. `%{time_total}` = how many seconds the download took. Online: [Write out - everything curl](https://everything.curl.dev/usingcurl/verbose/writeout.html) (a friendly guide with examples) and the [full list of variables](https://curl.se/docs/manpage.html#--write-out) in the official manual (or `man curl` in the terminal).

```bash
curl -s -o /dev/null -w 'time: %{time_total}s\n' http://localhost:8000/kiwi.gif
curl -s -o /dev/null -w 'time: %{time_total}s\n' http://localhost:8000/kiwi.gif
```
**Expected output**
```
time: 2.011179s
time: 2.006819s
```
Same object, same wait: 2 s every time.

---

## Part B. With the proxy

### Step 3. Start the proxy

Start `proxy_cache.py` in its pane.

### Step 4. Download the kiwi through the proxy, twice

**What it does:** `-x localhost:8080` = "use this proxy". `-D -` prints the response headers.

```bash
curl -s -D - -o /dev/null -w 'time: %{time_total}s\n' -x localhost:8080 http://localhost:8000/kiwi.gif
```
Run it **twice**. **Expected output** (last lines)
```
X-Cache: MISS
time: 2.009916s
```
```
X-Cache: HIT
time: 0.001106s
```
**Proxy log:**
```
MISS    http://localhost:8000/kiwi.gif   (hits=0, misses=1)
HIT     http://localhost:8000/kiwi.gif   (hits=1, misses=1)
```
**Origin server log:** only **one** request. The second time the origin was not even contacted.

### Step 5. What does the client send to the proxy?

```bash
curl -sv -o /dev/null -x localhost:8080 http://localhost:8000/kiwi.gif 2>&1 | grep '^> GET'
```
**Expected output**
```
> GET http://localhost:8000/kiwi.gif HTTP/1.1
```
The **full URL**, not only `/kiwi.gif`: on a MISS the proxy must know which server to ask.

---

## Part C. Real sites through the proxy

### Step 6. An http site

The first web site in history, still online in plain http:

```bash
curl -s -D - -o /dev/null -w 'time: %{time_total}s\n' -x localhost:8080 http://info.cern.ch/
```
Run it **twice**: `MISS`, then `HIT`. The proxy works with **any** site.

### Step 7. An https site

```bash
curl -s -o /dev/null -w '%{http_code}  time: %{time_total}s\n' -x localhost:8080 https://www.unipa.it/
```
**Expected output**
```
200  time: 0.085311s
```
**Proxy log:**
```
TUNNEL  www.unipa.it:443   (encrypted: cannot cache)
```
With https the client does not send `GET`, it sends `CONNECT www.unipa.it:443`: "open a tunnel to this server". The proxy then only copies encrypted bytes in both directions. It does not see the page, so it cannot keep a copy. Run it again: always `TUNNEL`, never `HIT`.

### Step 8. The browser through the proxy

In the browser (or system) network settings, set a **manual proxy**: `localhost`, port `8080`, for **both HTTP and HTTPS**. Browse normally for a minute and watch the proxy log. Which sites appear? Which lines are `HIT`/`MISS`, which are `TUNNEL`?

Remove the proxy setting at the end.

---

## Part D. The old copy

### Step 9. Change the page on the origin

1. Ask for the page through the proxy, **twice** (so the second time it is a `HIT`):
   ```bash
   curl -s -x localhost:8080 http://localhost:8000/index.html | grep Version
   ```
   ```
   <p>Version 1</p>
   ```
2. Open `www/index.html` in an editor, change `Version 1` into `Version 2`, save.
3. Ask again, through the proxy and then directly:
   ```bash
   curl -s -x localhost:8080 http://localhost:8000/index.html | grep Version
   curl -s http://localhost:8000/index.html | grep Version
   ```
   **Expected output**
   ```
   <p>Version 1</p>
   <p>Version 2</p>
   ```
The proxy keeps serving the **old copy**: once an object is in the cache, it never asks the origin again.

---

## Problem solving

**P1. Institutional cache (Kurose, Sec. 2.2.5)**
An institutional network is connected to the Internet with a **15 Mbps** access link. The LAN runs at **100 Mbps**. The browsers send on average **15 requests/s**, every object is **1 Mbit**. From the router on the Internet side of the access link to the origin servers and back takes **2 s** on average ("Internet delay").
a) Compute the traffic intensity on the LAN and on the access link. What happens to the delays?
b) Solution 1: upgrade the access link to **154 Mbps**. New traffic intensity? Average response time?
c) Solution 2: keep 15 Mbps and install a proxy in the LAN with **hit rate 0.4**. A hit takes about **0.01 s**. New traffic intensity on the access link? Average response time?
d) Which solution would you choose, and why?

**P2. Read the log**
The proxy printed this log (every MISS costs 2 s, every HIT about 0 s):
```
MISS    http://localhost:8000/index.html
MISS    http://localhost:8000/kiwi.gif
HIT     http://localhost:8000/index.html
HIT     http://localhost:8000/kiwi.gif
HIT     http://localhost:8000/kiwi.gif
MISS    http://localhost:8000/logo.png
HIT     http://localhost:8000/index.html
HIT     http://localhost:8000/logo.png
```
a) What is the hit rate?
b) How many requests reached the origin server?
c) How much waiting time did the proxy save?

**P3. Proxy and https**
a) Why can the proxy not cache `https://www.unipa.it/`?
b) Look at the `TUNNEL` lines: what does the proxy still know about your https browsing?
c) Today almost every site uses https. Is a proxy cache in the university network still useful?

**P4. The old copy**
a) In Step 9, why does `proxy_cache.py` never notice the change? Look at `do_GET`.
b) What could the proxy do to avoid serving old copies? What does it cost?
c) Is an old copy always a problem? Think of a logo and of a page with live football scores.

---

## Challenge: one proxy for the whole class

The teacher runs `origin_server.py` and `proxy_cache.py` and writes their IP address on the board. Every student downloads the kiwi **through the teacher's proxy**:

```bash
curl -s -D - -o /dev/null -w 'time: %{time_total}s\n' -x <TEACHER_IP>:8080 http://<TEACHER_IP>:8000/kiwi.gif
```

1. Who got `X-Cache: MISS`? How long did they wait, compared to the others?
2. The teacher shows the proxy log: what is the **hit rate of the class**? How many requests reached the origin?
3. Repeat with `index.html`. Who pays the MISS this time?

The more users share the proxy, the higher the hit rate.

---

## Solutions

<details>
<summary>P1</summary>

a) LAN: (15 req/s × 1 Mbit) / 100 Mbps = **0.15**, fine. Access link: (15 × 1) / 15 = **1**: the delays on the access link grow without limit; the response time becomes unacceptable.
b) Intensity (15 × 1) / 154 ≈ **0.1**: negligible delay on the access link. Response time ≈ **2 s** (the Internet delay). But upgrading the link is expensive.
c) Only 60% of the requests cross the access link: 0.6 × 15 = 9 Mbps, intensity **0.6**, small delay. Average response time ≈ 0.4 × 0.01 + 0.6 × (2 + 0.01) ≈ **1.2 s**.
d) The proxy: cheaper and even **faster** than the upgraded link (1.2 s vs 2 s).
</details>

<details>
<summary>P2</summary>

a) 8 requests, 5 HIT: hit rate = 5/8 = **0.625**.
b) Only the 3 MISS: **3 requests**.
c) Without proxy: 8 × 2 s = 16 s. With proxy: 3 × 2 s = 6 s. Saved: **10 s**.
</details>

<details>
<summary>P3</summary>

a) The proxy only sees encrypted bytes: not the page, not even the path (`/`). It cannot tell two requests apart, so it cannot keep and reuse a copy.
b) The **name of the server** and the port (`www.unipa.it:443`), when you connected and how much data passed. Not the pages or their content.
c) Much less than in the past: it can only cache the few http sites. This is why today caches are placed by the sites themselves, close to the users (CDNs): they own the certificates, so they can see and cache the content.
</details>

<details>
<summary>P4</summary>

a) On a HIT `do_GET` answers from `cache` and never contacts the origin: once an object is saved, it stays there until the proxy is restarted.
b) For example: keep a copy only for a limited time, or ask the origin "has this object changed since I copied it?" before using the copy. Both cost extra requests to the origin, so fewer savings.
c) A logo changes very rarely: an old copy is fine for a long time. Live scores change every minute: an old copy is wrong. How long a copy is good depends on the object.
</details>
