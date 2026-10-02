# 02.6 Head-of-Line blocking: HTTP/1.1 vs HTTP/2

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.2.5, HTTP/2)

## Concepts

1. On **one** HTTP/1.1 connection the objects travel **in a queue**, one after the other. If a **large** object (a video) is first, the small objects behind it **wait**, even if they could be sent at once. This is **Head-of-Line (HOL) blocking**.
2. The HTTP/1.1 workaround of the browsers: open **several TCP connections in parallel**. But every connection costs a handshake and resources, so browsers open **at most about 6** per server: with more objects than connections, HOL blocking comes back.
3. **HTTP/2**: **one** connection, but every response is cut into small pieces (**frames**) and the pieces of different objects are mixed. The small objects do not wait behind the large one, without opening more connections.
4. The **total** time does not change: it is set by the largest object. What changes is **when the small objects arrive**: the user sees icons and images at once, while the video is still loading.

## Files

| File | What it is |
|---|---|
| `server.py` | A web server, port **8000**, with 3 objects of different size. It logs when every request **arrives** and when it is **answered** |
| `arrival.py` | A tiny helper: it writes in front of every line printed by curl **how many seconds after the start** it arrived |

In `server.py` the size of each object is turned into a sending time (bigger file = longer to send):
```python
SIZES = {                              # object -> seconds to send it
    '/large': 3,                       # a large file (a video)
    '/small': 1,                       # a small file (an image)
    '/tiny':  0,                       # a tiny file (an icon)
}
```

**What is hypercorn?** Python's `http.server`, used in the other folders, speaks only HTTP/1.x. **Hypercorn** is a Python web server that speaks **HTTP/1.1 and HTTP/2**: `server.py` uses it to answer in both versions. We use it as a black box, there is no need to know how it works inside. Online: [hypercorn documentation](https://hypercorn.readthedocs.io/). It is installed by `setup_env.sh` (`requirements.txt`).

## Setup

Use two tmux panes: the **server** on the left, the **client commands** on the right. Start `server.py` in the left pane. It prints:
```
22:44:15.500  Server on http://localhost:8000 (HTTP/1.1 and HTTP/2)
```

### The client command

In every step curl asks for the **same 3 objects** (`/large`, `/small`, `/tiny`, in this order) with **one** command. Only the options in the middle change.

| Option | What it does |
|---|---|
| `'.../{large,small,tiny}'` | curl asks for `/large`, `/small`, `/tiny`: **3 requests** with one command ([URL globbing](https://everything.curl.dev/cmdline/urls/globbing.html)) |
| `-s` | **silent**: hide the progress bar |
| `-o /dev/null` | throw away the bodies |
| `-w '...'` | **write-out**: when an object is complete, curl prints this text. `%{...}` are **curl variables** that curl fills in: `%{url_effective}` = the URL, `%{local_port}` = the client port (same port = same connection), `%{http_version}` = the HTTP version used. `%{stderr}` = print it on the error channel, **at once** (the normal output would be printed only at the end) ([write-out](https://everything.curl.dev/usingcurl/verbose/writeout.html)) |
| `2>&1 \| python arrival.py` | send curl's lines (error channel) to `arrival.py`, which adds the arrival time |
| `--http1.1` | use HTTP/1.1 |
| `--parallel` | do **not** wait for a request to finish before sending the next one ([parallel transfers](https://everything.curl.dev/cmdline/urls/parallel.html)) |
| `--parallel-max 2` | at most **2** transfers at the same time |
| `--http2` | use **HTTP/2**: curl first **asks** the server to switch to it ([HTTP/2 in curl](https://everything.curl.dev/http/versions/http2.html)) |
| `--http2-prior-knowledge` | use **HTTP/2** at once, **without asking**: curl already knows the server speaks it |

All curl options: [official curl manual](https://curl.se/docs/manpage.html) (or `man curl`).

### How to read the results

- **Client output**: one line per object, with **after how many seconds it arrived**, and the **client port**: same port = same TCP connection, so **count the different ports** to know how many connections curl opened.
- **Server log**: when every request **arrived** at the server and when it was **answered**.

---

## Step 1. HTTP/1.1, one connection: HOL blocking

```bash
curl --http1.1 -s -o /dev/null -w '%{stderr}%{url_effective}  port %{local_port}  HTTP/%{http_version}\n' 'http://localhost:8000/{large,small,tiny}' 2>&1 | python arrival.py
```
**Client output**
```
after  3.0 s   http://localhost:8000/large  port 59305  HTTP/1.1
after  4.0 s   http://localhost:8000/small  port 59305  HTTP/1.1
after  4.0 s   http://localhost:8000/tiny  port 59305  HTTP/1.1
```
**Server log**
```
22:44:15.652  [port 59305]  HTTP/1.1  /large arrived
22:44:18.655  [port 59305]  HTTP/1.1  /large answered
22:44:18.656  [port 59305]  HTTP/1.1  /small arrived
22:44:19.657  [port 59305]  HTTP/1.1  /small answered
22:44:19.658  [port 59305]  HTTP/1.1  /tiny  arrived
22:44:19.658  [port 59305]  HTTP/1.1  /tiny  answered
```

One connection, one object after the other: `/large` 3 s, then `/small` 1 s more, then `/tiny`. The tiny icon could be sent at once, but it arrives **after 4 s**: it waited in the queue behind the other two. Its request even **reaches the server** only at the end: curl (like modern browsers) does not send the next request on the same HTTP/1.1 connection before the previous answer is complete. Even if it did (**pipelining**, Kurose Sec. 2.2.2), HTTP/1.1 must send the answers **in the same order** as the requests: `/tiny` would still wait behind `/large`.

## Step 2. HTTP/1.1, parallel connections: the browser workaround

Add `--parallel`:
```bash
curl --http1.1 --parallel -s -o /dev/null -w '%{stderr}%{url_effective}  port %{local_port}  HTTP/%{http_version}\n' 'http://localhost:8000/{large,small,tiny}' 2>&1 | python arrival.py
```
**Client output**
```
after  0.0 s   http://localhost:8000/tiny  port 59311  HTTP/1.1
after  1.0 s   http://localhost:8000/small  port 59310  HTTP/1.1
after  3.0 s   http://localhost:8000/large  port 59309  HTTP/1.1
```
**Server log**
```
22:44:22.337  [port 59309]  HTTP/1.1  /large arrived
22:44:22.338  [port 59310]  HTTP/1.1  /small arrived
22:44:22.338  [port 59311]  HTTP/1.1  /tiny  arrived
22:44:22.338  [port 59311]  HTTP/1.1  /tiny  answered
22:44:23.340  [port 59310]  HTTP/1.1  /small answered
22:44:25.340  [port 59309]  HTTP/1.1  /large answered
```

Now every object arrives after its own time: `/tiny` at once, `/small` after 1 s, `/large` after 3 s. But look at the ports: **3 different ports = 3 connections**: with HTTP/1.1, the only way to send requests at the same time is to open more connections. Here they are free (localhost); on a real network each one costs a TCP handshake (and a TLS one with https).

## Step 3. HTTP/1.1 with a connection limit: HOL blocking comes back

A browser opens at most about 6 connections per server. To see the effect with only 3 objects we use a limit of **2** (`--parallel-max 2`):
```bash
curl --http1.1 --parallel --parallel-max 2 -s -o /dev/null -w '%{stderr}%{url_effective}  port %{local_port}  HTTP/%{http_version}\n' 'http://localhost:8000/{large,small,tiny}' 2>&1 | python arrival.py
```
**Client output**
```
after  1.0 s   http://localhost:8000/small  port 59315  HTTP/1.1
after  1.0 s   http://localhost:8000/tiny  port 59315  HTTP/1.1
after  3.0 s   http://localhost:8000/large  port 59314  HTTP/1.1
```
**Server log**
```
22:44:28.037  [port 59314]  HTTP/1.1  /large arrived
22:44:28.037  [port 59315]  HTTP/1.1  /small arrived
22:44:29.040  [port 59315]  HTTP/1.1  /small answered
22:44:29.041  [port 59315]  HTTP/1.1  /tiny  arrived
22:44:29.041  [port 59315]  HTTP/1.1  /tiny  answered
22:44:31.039  [port 59314]  HTTP/1.1  /large answered
```

Only **2 ports = 2 connections**: one busy with `/large`, the other with `/small`. `/tiny` must wait in the queue of `/small`: it arrives **after 1 s** instead of at once. With a real page (a few videos, dozens of images, 6 connections) it is the same.

## Step 4. HTTP/2: one connection, no HOL blocking

The same 3 objects, with `--http2`:
```bash
curl --http2 --parallel -s -o /dev/null -w '%{stderr}%{url_effective}  port %{local_port}  HTTP/%{http_version}\n' 'http://localhost:8000/{large,small,tiny}' 2>&1 | python arrival.py
```
**Client output**
```
after  0.0 s   http://localhost:8000/tiny  port 59317  HTTP/2
after  1.0 s   http://localhost:8000/small  port 59317  HTTP/2
after  3.0 s   http://localhost:8000/large  port 59317  HTTP/2
```
**Server log**
```
22:44:33.726  [port 59317]  HTTP/2    /large arrived
22:44:33.727  [port 59317]  HTTP/2    /small arrived
22:44:33.727  [port 59317]  HTTP/2    /tiny  arrived
22:44:33.727  [port 59317]  HTTP/2    /tiny  answered
22:44:34.729  [port 59317]  HTTP/2    /small answered
22:44:36.729  [port 59317]  HTTP/2    /large answered
```

**One port = one connection only**, and every object arrives after its own time, as in Step 2. All 3 requests reach the server together **on the same connection**: HTTP/2 mixes the answers, so the small ones pass the large one.

> `--parallel` does not mean "more connections": it means "send the requests at the same time". With HTTP/1.1 this needs more connections (Steps 2 and 3); with HTTP/2 it happens on one connection.

**Why `--parallel`?** HTTP/2 can mix the answers only if **several requests are open at the same time** on the connection. A browser sends all the requests of a page at once (it reads the HTML, then asks for all the images). curl, by default, sends one request after the other: without `--parallel` there is nothing to mix, and HTTP/2 behaves like Step 1. Try it:
```bash
curl --http2 -s -o /dev/null -w '%{stderr}%{url_effective}  port %{local_port}  HTTP/%{http_version}\n' 'http://localhost:8000/{large,small,tiny}' 2>&1 | python arrival.py
```
**Client output**
```
after  3.0 s   http://localhost:8000/large  port 59363  HTTP/2
after  4.0 s   http://localhost:8000/small  port 59363  HTTP/2
after  4.0 s   http://localhost:8000/tiny  port 59363  HTTP/2
```
**Server log**
```
22:48:08.163  [port 59363]  HTTP/2    /large arrived
22:48:11.168  [port 59363]  HTTP/2    /large answered
22:48:11.169  [port 59363]  HTTP/2    /small arrived
22:48:12.173  [port 59363]  HTTP/2    /small answered
22:48:12.174  [port 59363]  HTTP/2    /tiny  arrived
22:48:12.175  [port 59363]  HTTP/2    /tiny  answered
```
HTTP/2, but one request at a time: `/tiny` waits 4 s again.

**How did curl switch to HTTP/2?** `-v` (verbose) shows the exchange; `2>&1 | grep` keeps only the interesting lines:
```bash
curl --http2 -sv -o /dev/null http://localhost:8000/tiny 2>&1 | grep -E '^> (GET|Upgrade)|^< HTTP'
```
**Client output**
```
> GET /tiny HTTP/1.1
> Upgrade: h2c
< HTTP/1.1 101
< HTTP/2 200
```
The first request is HTTP/1.1 and **asks** to switch (`Upgrade: h2c` = HTTP/2 without encryption). The server says yes with `101 Switching Protocols`. From there on, the connection speaks HTTP/2.

> The server log does not show this switch: hypercorn does it by itself, before calling our code. Our log already sees HTTP/2.

## Step 5. HTTP/2 forced: `--http2-prior-knowledge`

The same as Step 4, but curl **already knows** that the server speaks HTTP/2: no question, HTTP/2 from the first byte.
```bash
curl --http2-prior-knowledge --parallel -s -o /dev/null -w '%{stderr}%{url_effective}  port %{local_port}  HTTP/%{http_version}\n' 'http://localhost:8000/{large,small,tiny}' 2>&1 | python arrival.py
```
**Client output**
```
after  0.0 s   http://localhost:8000/tiny  port 59319  HTTP/2
after  1.0 s   http://localhost:8000/small  port 59319  HTTP/2
after  3.0 s   http://localhost:8000/large  port 59319  HTTP/2
```
**Server log**
```
22:44:39.418  [port 59319]  HTTP/2    /large arrived
22:44:39.418  [port 59319]  HTTP/2    /small arrived
22:44:39.418  [port 59319]  HTTP/2    /tiny  arrived
22:44:39.419  [port 59319]  HTTP/2    /tiny  answered
22:44:40.421  [port 59319]  HTTP/2    /small answered
22:44:42.420  [port 59319]  HTTP/2    /large answered
```

Same result as Step 4. The difference is only at the start:
```bash
curl --http2-prior-knowledge -sv -o /dev/null http://localhost:8000/tiny 2>&1 | grep -E '^> (GET|Upgrade)|^< HTTP'
```
**Client output**
```
> GET /tiny HTTP/2
< HTTP/2 200
```
No `Upgrade`, no `101`: the very first request is already HTTP/2.

> On real **https** sites the choice of HTTP/2 happens during the TLS handshake (no `Upgrade`, no `101`): `--http2` does it by itself, like a browser.

## Summary

| | Connections (ports) | `/tiny` arrives after | `/small` after | `/large` after |
|---|---|---|---|---|
| Step 1. HTTP/1.1 | 1 | **4 s** (HOL) | **4 s** (HOL) | 3 s |
| Step 2. HTTP/1.1 `--parallel` | **3** | 0 s | 1 s | 3 s |
| Step 3. HTTP/1.1 `--parallel`, max 2 | 2 | **1 s** (HOL) | 1 s | 3 s |
| Steps 4 and 5. HTTP/2 | **1** | 0 s | 1 s | 3 s |

`/large` always arrives after 3 s: the time to get **everything** does not get shorter. HTTP/2 makes every object arrive after **its own** time, as with many connections, but with **one** connection.

---

## Questions

**Q1.** `/large` always arrives after 3 s. So what did we gain in Steps 2, 4 and 5?

**Q2.** Step 2 solves HOL blocking too. Why don't browsers simply open 100 connections to the same server?

**Q3.** In Step 4 all the objects share **one** TCP connection. TCP delivers the bytes in order: what happens to **all** the objects if one TCP segment is lost and must be sent again?

---

## Solutions

<details>
<summary>Q1</summary>

The time for the whole page is set by `/large` (3 s) in every case. What changes is **when the smaller objects arrive**: in Step 1 the icon waits 4 s, in Steps 2, 4 and 5 it arrives at once. In a web page the user sees icons and images immediately, while the video is still loading.
</details>

<details>
<summary>Q2</summary>

Every connection costs a TCP handshake (and with https a TLS handshake), memory on the server, and it competes with the others for the network. Browsers use at most about 6 connections per server, and Step 3 shows what happens when the connections are not enough. HTTP/2 gets the result of Step 2 with **one** connection.
</details>

<details>
<summary>Q3</summary>

All the objects wait until the lost segment arrives, because TCP delivers bytes only in order: HOL blocking comes back, at the TCP level. This is one of the reasons for **HTTP/3**, which runs on QUIC (over UDP) instead of TCP.
</details>
