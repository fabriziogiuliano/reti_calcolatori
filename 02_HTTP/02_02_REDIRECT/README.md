# 02.2 HTTP Redirects (3xx + `Location`)

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.2.3)

## Concepts

1. Status codes come in classes: `2xx` success, `3xx` redirection, `4xx` client error, `5xx` server error.
2. A `3xx` response does not contain the page: it tells the client where to go, in the `Location` header. The client must send a new request.
3. Every hop costs a new request, often a new TCP connection (and a new TLS handshake): more RTTs before the page arrives.
4. `301 Moved Permanently` vs `302 Found` (temporary): with a 301 the client may remember the new URL, with a 302 it must ask the old URL again next time.
5. A client that follows redirects automatically must stop after N hops, or a loop (`A -> A`) runs forever.

## Files

| File | What it is |
|---|---|
| `redirect_server.py` | Local web server that answers with redirects ([`http.server`](https://docs.python.org/3/library/http.server.html), Python standard library) |
| `redirect_server_raw.py` | The same server written with bare sockets |
| `redirect.py` | Minimal client that follows redirects, like a browser |

---

## Part A. Redirects on real sites

### Step 1. Look at one redirect, by hand

`ncat` opens a TCP connection to `unipa.it`, port 80, and lets you type the HTTP request yourself, as in 02_01_SIMPLE. `-C` turns every Enter into `\r\n`, the line ending HTTP requires.

```bash
ncat -C unipa.it 80
```
Then paste the request. The empty line at the end is part of it: it closes the headers. `Connection: close` asks the server to close the connection after the answer.
```
GET / HTTP/1.1
Host: unipa.it
Connection: close

```
**Expected output**
```
HTTP/1.1 302 Found
Date: Fri, 02 Oct 2026 14:13:17 GMT
Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1g mod_fcgid/2.3.9
Location: https://www.unipa.it/
Content-Length: 205
Connection: close
Content-Type: text/html; charset=iso-8859-1

<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>302 Found</title>
</head><body>
<h1>Found</h1>
<p>The document has moved <a href="https://www.unipa.it/">here</a>.</p>
</body></html>
```
`302` means "go elsewhere", and `Location` says where. The body is not the home page: it is only a short note for humans. Note the change from `http` to `https`.

> Tip: paste the request quickly. If the headers arrive too slowly, the server closes the connection.

### Step 2. Follow the redirect, by hand

You are now the browser. `Location` says `https://www.unipa.it/`: a different host, a different port (443) and TLS. The old connection is closed, so you must open a new one. `--ssl` makes ncat do the TLS handshake for you.

```bash
ncat -C --ssl www.unipa.it 443
```
This time use `HEAD` instead of `GET`: you get only the headers (the home page is more than 500 KB).
```
HEAD / HTTP/1.1
Host: www.unipa.it
Connection: close

```
**Expected output** (first lines)
```
HTTP/1.1 200 OK
Date: Fri, 02 Oct 2026 11:52:06 GMT
Server: OpenCms/8.0.4
...
```
So getting one page took two connections and two requests.

### Step 3. Let curl follow the chain

Here curl does Steps 1 and 2 for you. `-I` asks only for the headers (`HEAD`), `-L` follows every `Location` until a non-3xx answer.

```bash
curl -IL http://unipa.it
```
Only the important lines:
```bash
curl -sIL http://unipa.it | grep -iE '^(HTTP|location)'
```
**Expected output**
```
HTTP/1.1 302 Found
Location: https://www.unipa.it/
HTTP/1.1 200 OK
```
These are the same two responses you got by hand.

### Step 4. A permanent redirect

```bash
curl -sIL http://google.com | grep -iE '^(HTTP|location)'
```
**Expected output**
```
HTTP/1.1 301 Moved Permanently
Location: http://www.google.com/
HTTP/1.1 200 OK
```
`301`: google.com has moved to www.google.com for good.

---

## Part B. Our own redirect server

From here on we need two programs at the same time: a server and a client. Split the terminal in two with tmux: the server runs in the left pane, the client commands go in the right pane.

### Step 5. Start the server (left pane)

`redirect_server.py` starts a web server on your own machine (`localhost`), port 8000. It does not serve real pages: for most paths it answers only with a redirect. It keeps running and prints one line for every request it receives.

Start `redirect_server.py` in the left pane. It prints:
```
Listening on http://localhost:8000 ...
```
The server knows these paths:

| Path | Answer |
|---|---|
| `/a` | `301` -> `/b` |
| `/b` | `302` -> `/c` |
| `/c` | `200` + a small page |
| `/loop` | `302` -> `/loop` (itself) |
| `/unipa` | `302` -> `https://www.unipa.it/` |
| anything else | `404` |

### Step 6. Follow the chain by hand (right pane)

You play the browser again, this time against our server.

```bash
ncat -C localhost 8000
```
```
GET /a HTTP/1.1
Host: localhost:8000

```
**Expected output**
```
HTTP/1.0 301 Moved Permanently
Server: BaseHTTP/0.6 Python/3.11.17
Date: Fri, 02 Oct 2026 14:13:17 GMT
Location: /b
```
The server answers with `HTTP/1.0` and closes the connection by itself: no `Connection: close` needed.

`Location: /b` is a relative URL: same scheme, host and port, new path. Open a new connection with the same `ncat` command and ask for `/b`, then for `/c`, until you get:
```
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.11.17
Date: Fri, 02 Oct 2026 14:13:17 GMT
Content-Type: text/html

<h1>You made it!</h1>
```
Look at the server log: one line for each request you typed.

> Note: try again with `HEAD /a HTTP/1.1` instead of `GET`. The answer is `501 Unsupported method ('HEAD')`: our server only implements `GET` (`do_GET`). A `5xx` code means "the server cannot do it".

### Step 7. Let curl follow the chain

`-i` prints headers and body of every response, `-L` follows the redirects. (We use `-i`, not `-I`: our server does not support `HEAD`.)

```bash
curl -iL http://localhost:8000/a
```
**Expected output**
```
HTTP/1.0 301 Moved Permanently
...
Location: /b

HTTP/1.0 302 Found
...
Location: /c

HTTP/1.0 200 OK
...
<h1>You made it!</h1>
```
**Server log:** one line per request. Every hop is a new request.
```
127.0.0.1 - - [02/Oct/2026 16:06:21] "GET /a HTTP/1.1" 301 -
127.0.0.1 - - [02/Oct/2026 16:06:21] "GET /b HTTP/1.1" 302 -
127.0.0.1 - - [02/Oct/2026 16:06:21] "GET /c HTTP/1.1" 200 -
```

### Step 8. A redirect loop

```bash
curl -sSL --max-redirs 5 http://localhost:8000/loop
```
**Expected output**
```
curl: (47) Maximum (5) redirects followed
```
curl stops by itself (default limit: 50). Count the `GET /loop` lines in the server log. Then open `http://localhost:8000/loop` in the browser: what error does it show?

---

## Part C. A client that follows redirects

Keep the server running in the left pane.

### Step 9. Run `redirect.py` on our server

`redirect.py` is the socket client of 02_01_SIMPLE, inside a loop: if the answer is `3xx`, read `Location` and send a new request. It takes the starting URL as argument (default: `http://google.com`).

In the right pane, run `redirect.py` with the URL `http://localhost:8000/a`.

**Expected output**
```
[0] GET http://localhost:8000/a
    <- HTTP/1.0 301 Moved Permanently
    Location: /b
[1] GET http://localhost:8000/b
    <- HTTP/1.0 302 Found
    Location: /c
[2] GET http://localhost:8000/c
    <- HTTP/1.0 200 OK
```

### Step 10. Loop, other host, real site

Run `redirect.py` again with each of these URLs:

- `http://localhost:8000/loop`: the loop, the client must stop by itself;
- `http://localhost:8000/unipa`: the chain leaves our machine;
- `http://unipa.it`: a real site, no local server involved.

**Expected output** (last lines with `/loop`)
```
[5] GET http://localhost:8000/loop
    <- HTTP/1.0 302 Found
    Location: /loop
STOP: more than 5 redirects. Is it a loop?
```
With `/unipa` the chain leaves our machine: hop `[1]` goes to `https://www.unipa.it/` on port 443, with TLS.

Read the code: find (1) where the new TCP connection is opened, (2) where `Location` is read, (3) where the hop limit is enforced.

---

## Part D. Under the hood: the server without libraries

### Step 11. Run the socket version

`redirect_server_raw.py` is the same server (same paths, same port 8000) written with bare sockets: every byte of the response is written by hand.

Stop `redirect_server.py` in the left pane (`Ctrl+c`): two servers cannot listen on the same port. Start `redirect_server_raw.py` in its place, then in the right pane:
```bash
curl -iL http://localhost:8000/a
```
**Server log**
```
Listening on http://localhost:8000 ...
('127.0.0.1', 53375) GET /a HTTP/1.1
('127.0.0.1', 53377) GET /b HTTP/1.1
('127.0.0.1', 53379) GET /c HTTP/1.1
```
Compare the two server files side by side:

| `redirect_server.py` | `redirect_server_raw.py` |
|---|---|
| `HTTPServer(('', 8000), ...)` | `bind()` + `listen()` + `accept()` |
| `self.path` | `request.split('\r\n')[0].split(' ')[1]` |
| `send_response(302)` | `"HTTP/1.1 302 Found\r\n"` |
| `send_header('Location', '/b')` | `"Location: /b\r\n"` |
| `end_headers()` | `"\r\n"` |

Look at the client port (`53375`, `53377`, `53379`): what does it tell you?

---

## Problem solving

**P1. How much does a redirect cost?**
A user types `unipa.it` in the browser (so `http://unipa.it/`). RTT to the server = 30 ms. Assume: DNS lookup = 1 RTT per new host name, TCP handshake = 1 RTT, TLS handshake = 1 RTT, HTTP request/response = 1 RTT. Ignore transmission times.
a) How many RTTs before the page starts to arrive? How many ms?
b) And if the user typed `https://www.unipa.it/` directly?
c) What percentage of the time is lost because of the redirect?

**P2. Relative `Location`**
The client requested `http://localhost:8000/docs/old/page`. Which URL must it request next if the server answers with:
a) `Location: /new`  b) `Location: new`  c) `Location: ../new`  d) `Location: https://www.unipa.it/`

**P3. 301 or 302?**
Which code would you use, and why?
a) The whole site moves from `http://` to `https://` forever.
b) A user who is not logged in asks for `/profile` and must be sent to `/login`.
c) The home page is replaced by a "site under maintenance" page for one night.

**P4. Who is at fault?**
For each code say: success, redirect, client error or server error; and who should fix the problem.
`200`, `301`, `302`, `400`, `404`, `501`, `505`

**P5. How many connections?**
In Step 11 the client port changes at every hop. How many TCP connections did `curl -iL http://localhost:8000/a` open? Why does the server force a new one every time?

---

## Challenge: the secret chain

Work in pairs.

1. Student A edits `ROUTES` in `redirect_server.py` and builds a secret chain (at least 4 hops, mixing `301` and `302`, ending with a `200`). Then restarts the server.
2. Student B knows only the start path (e.g. `/start`) and must rebuild the whole chain using only curl, without looking at the code. Draw it on paper: `/start --301--> ... --200`.
3. Swap roles.

To play on two different machines, B uses A's IP address instead of `localhost` (`ifconfig | grep 'inet '` on macOS, `hostname -I` on Linux):
```bash
curl -iL http://<IP_OF_A>:8000/start
```

Bonus: A hides a loop in the chain (e.g. `/x -> /y -> /x`). Can B find it with `curl -iL --max-redirs 10`?

---

## Solutions

<details>
<summary>P1</summary>

a) Hop 0, `http://unipa.it/`: DNS (1) + TCP (1) + HTTP (1) = 3 RTT. Hop 1, `https://www.unipa.it/` (new host, port 443): DNS (1) + TCP (1) + TLS (1) + HTTP (1) = 4 RTT. Total 7 RTT = 210 ms.
b) Only hop 1: 4 RTT = 120 ms.
c) 90 ms out of 210 ms, about 43% of the time is spent on the redirect.
</details>

<details>
<summary>P2</summary>

a) `http://localhost:8000/new`
b) `http://localhost:8000/docs/old/new`
c) `http://localhost:8000/docs/new`
d) `https://www.unipa.it/` (absolute: used as it is)

This is exactly what `urljoin()` does in `redirect.py`.
</details>

<details>
<summary>P3</summary>

a) 301: the move is permanent; browsers and search engines can update the address and skip the old one.
b) 302: temporary, it depends on the user's state; once logged in, `/profile` must work again.
c) 302: tomorrow the home page is back; a 301 would make browsers remember the maintenance page.
</details>

<details>
<summary>P4</summary>

`200` success. `301`, `302` redirect (nothing to fix, the client follows `Location`). `400` Bad Request and `404` Not Found: client error (wrong request or wrong URL). `501` Not Implemented and `505` HTTP Version Not Supported: server error (the server cannot handle that method or that version).
</details>

<details>
<summary>P5</summary>

3 connections, one per hop (`/a`, `/b`, `/c`): every new connection gets a new client port. The raw server calls `conn.close()` after every response, so the client cannot reuse the connection. Reusing it (persistent connections) is the topic of 02_05_PERSISTENT_HTTP.
</details>
