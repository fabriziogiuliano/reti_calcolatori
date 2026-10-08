# 02.0 curl: an HTTP client in the terminal

curl is a program that talks HTTP (and many other protocols) from the command line. It works like a browser without graphics: it sends a request, receives the response, and shows you all of it, including what a browser hides.

Why curl? It is a professional tool, open source since 1998 and already installed on macOS, Windows and Linux. Developers use it every day to test web APIs, system administrators to check sites and servers, and its library (libcurl) runs inside phones, cars and countless programs. Browsers can even turn any request into a curl command: in the developer tools, *Network* tab, right click on a request, then *Copy as cURL* ([how it works](https://everything.curl.dev/cmdline/copyas.html)). More on the project: [curl.se](https://curl.se/).

We start from the simplest command and add one option at a time. At the end you will know every option used in the lab folders, from `02_01` to `02_06`.

- Friendly guide with examples: [everything curl](https://everything.curl.dev/)
- All the options: [official curl manual](https://curl.se/docs/manpage.html) (or `man curl` in the terminal)

We use `example.com`, a site made for examples, and a few real sites.

---

## Level 1. See the response

### Step 1. Ask for a page

```bash
curl http://example.com
```
**Output** (beginning)
```
<!doctype html><html lang=en><head><meta charset=utf-8>...<title>Example Domain</title>...
```
curl sends a `GET` request and prints the body of the response, the HTML a browser would draw.

### Step 2. `-i`: headers and body

```bash
curl -i http://example.com
```
**Output** (beginning)
```
HTTP/1.1 200 OK
Date: Fri, 02 Oct 2026 21:08:49 GMT
Content-Type: text/html; charset=utf-8
Connection: keep-alive
Server: cloudflare
...

<!doctype html><html lang=en>...
```
`-i` (*include*) prints the status line and the headers of the response before the body.

### Step 3. `-I`: only the headers

```bash
curl -I http://example.com
```
**Output**
```
HTTP/1.1 200 OK
Date: Fri, 02 Oct 2026 21:08:49 GMT
Content-Type: text/html; charset=utf-8
Connection: keep-alive
Server: cloudflare
...
```
`-I` sends a `HEAD` request instead of `GET`, and the server answers with the headers only.

### Step 4. `-v`: the whole conversation

```bash
curl -v http://example.com
```
**Output** (beginning)
```
* Host example.com:80 was resolved.
*   Trying 104.20.23.154:80...
* Connected to example.com (104.20.23.154) port 80
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/8.7.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Date: Fri, 02 Oct 2026 21:08:49 GMT
< Content-Type: text/html; charset=utf-8
...
```
`-v` (*verbose*) shows the whole exchange. The first character of each line tells what the line is:

| Line starts with | Meaning |
|---|---|
| `*` | what curl is doing (DNS, TCP connection, TLS...) |
| `>` | what the client sends (the request) |
| `<` | what the client receives (the response headers) |

---

## Level 2. Control the output

### Step 5. `-s`: silent

When the output goes to a pipe (`|`) or a file, curl shows a progress bar:
```bash
curl http://example.com | head -c 50
```
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   577    0   577    0     0   5622      0 --:--:-- --:--:-- --:--:--  5656
<!doctype html><html lang=en><head><meta charset=u
```
`-s` (*silent*) hides it:
```bash
curl -s http://example.com | head -c 50
```
```
<!doctype html><html lang=en><head><meta charset=u
```
`-S` (*show error*), used together with `-s`, still prints the errors.

> Short options can be joined: `-sv` is `-s -v`, `-sIL` is `-s -I -L`, `-sSL` is `-s -S -L`. In the lab folders `-s` is almost always joined to other options: whenever the output goes to a pipe (`|`) or `-w` prints something, it keeps the progress bar out of the way.

### Step 6. `-o`: where the body goes

```bash
curl -s -o page.html http://example.com
ls -l page.html
```
```
-rw-r--r--  1 fabrizio  wheel  577 Oct  2 23:08 page.html
```
`-o file` (*output*) saves the body in a file. `-o /dev/null` throws it away, which is useful when we only care about headers or times.

### Step 7. `2>&1 | grep`: keep only some lines of `-v`

`-v` writes on the error channel (stderr), not on the normal output. `2>&1` sends it to the normal output, so that `grep` can filter it:
```bash
curl -sv -o /dev/null http://example.com 2>&1 | grep -E '^> GET|^< HTTP'
```
**Output**
```
> GET / HTTP/1.1
< HTTP/1.1 200 OK
```
Only the request line and the status line are left. `grep -E 'A|B'` keeps the lines that match A or B, and `-i` ignores upper/lower case.

### Step 8. `-w`: print what you want

```bash
curl -s -o /dev/null -w 'code: %{http_code}  time: %{time_total}s\n' http://example.com
```
**Output**
```
code: 200  time: 0.068087s
```
`-w` (*write-out*) prints a text after the transfer. The parts `%{...}` are curl variables, filled in by curl. The most useful ones:

| Variable | Meaning |
|---|---|
| `%{http_code}` | the status code (200, 404...) |
| `%{time_total}` | seconds for the whole transfer |
| `%{url_effective}` | the URL actually requested |
| `%{local_port}` | the client port: the same port means the same TCP connection |
| `%{num_connects}` | `1` if a new connection was opened, `0` if an old one was reused |
| `%{http_version}` | the HTTP version of the response |

Full list: [write-out in everything curl](https://everything.curl.dev/usingcurl/verbose/writeout.html).

---

## Level 3. Change the request

### Step 9. `-H`: add or change a header

```bash
curl -sv -o /dev/null -H 'User-Agent: my-browser' http://example.com 2>&1 | grep '^> '
```
**Output**
```
> GET / HTTP/1.1
> Host: example.com
> Accept: */*
> User-Agent: my-browser
>
```
`-H 'Name: value'` (*header*) puts that header in the request. Here we pretend to be another browser.

### Step 10. `-L`: follow redirects

```bash
curl -sI http://google.com | head -3
```
```
HTTP/1.1 301 Moved Permanently
Location: http://www.google.com/
Content-Type: text/html; charset=UTF-8
```
Without options curl does not follow the redirect: it shows the `301` and stops. With `-L` (*location*) it follows every `Location`:
```bash
curl -sIL http://google.com | grep -iE '^(HTTP|location)'
```
```
HTTP/1.1 301 Moved Permanently
Location: http://www.google.com/
HTTP/1.1 200 OK
```
`--max-redirs N` sets the maximum number of redirects to follow.

### Step 11. `-c` and `-b`: cookies

The server gives a cookie with `Set-Cookie`:
```bash
curl -sI https://www.unipa.it | grep -i '^set-cookie'
```
```
Set-Cookie: JSESSIONID=8A1115B36DBCED5DA3541C8FF5FA0584; Path=/; HttpOnly
```
`-c file` (*cookie jar*) saves the cookies received, `-b file` sends them back. `-b 'name=value'` sends a cookie written by hand:
```bash
curl -s -o /dev/null -c cookies.txt https://www.unipa.it
curl -sv -o /dev/null -b cookies.txt https://www.unipa.it 2>&1 | grep -i '^> cookie'
```
```
> Cookie: JSESSIONID=35D8D3312AA14B9A782E8AE052F89A42
```
The second request carries the cookie saved by the first one, as a browser does.

### Step 12. `-x`: use a proxy

```bash
curl -x localhost:8080 http://example.com
```
`-x host:port` sends the request to a proxy instead of directly to the site. It needs a proxy running on that port: we build one in `02_03_PROXY_CACHE`.

---

## Level 4. Many requests

### Step 13. Many URLs in one command

```bash
curl -s -o /dev/null -w '%{url_effective}  %{http_code}\n' 'http://example.com/?page=[1-3]'
```
**Output**
```
http://example.com/?page=1  200
http://example.com/?page=2  200
http://example.com/?page=3  200
```
`[1-3]` makes curl ask for 3 URLs, one after the other. `{a,b}` works with names:
```bash
curl -s -o /dev/null -w '%{url_effective}  %{http_code}\n' 'http://example.com/{a,b}'
```
```
http://example.com/a  404
http://example.com/b  404
```
Always put the URL between quotes `'...'`: `[ ]` and `{ }` have a special meaning for the shell too. ([URL globbing](https://everything.curl.dev/cmdline/urls/globbing.html))

### Step 14. Same connection or a new one?

```bash
curl -s -o /dev/null -w 'port %{local_port}  new conn: %{num_connects}\n' 'http://example.com/?page=[1-3]'
```
**Output**
```
port 59639  new conn: 1
port 59639  new conn: 0
port 59639  new conn: 0
```
The client port is the same, and `new conn: 0` after the first: curl reused the same TCP connection for the 3 requests.

### Step 15. Choose the HTTP version

```bash
curl --http1.0 -sv -o /dev/null https://example.com 2>&1 | grep -E '^> GET|^< HTTP'
curl --http1.1 -sv -o /dev/null https://example.com 2>&1 | grep -E '^> GET|^< HTTP'
curl --http2   -sv -o /dev/null https://example.com 2>&1 | grep -E '^> GET|^< HTTP'
```
**Output**
```
> GET / HTTP/1.0
< HTTP/1.1 200 OK

> GET / HTTP/1.1
< HTTP/1.1 200 OK

> GET / HTTP/2
< HTTP/2 200
```
The option sets the version of the request (the `>` line). With `--http1.0` the server still answers `HTTP/1.1`, which is allowed: the server tells which version it supports.

### Step 16. `--parallel`: all the requests at the same time

```bash
curl --http1.1 --parallel -s -o /dev/null -w 'port %{local_port}  new conn: %{num_connects}\n' 'https://example.com/?page=[1-3]'
```
**Output**
```
port 59644  new conn: 1
port 59645  new conn: 1
port 59643  new conn: 1
```
Without `--parallel` curl sends one request after the other (Step 14). With `--parallel` it sends them at the same time, and with HTTP/1.1 that needs 3 connections (3 ports). ([parallel transfers](https://everything.curl.dev/cmdline/urls/parallel.html))

### Step 17. Total time of a command

```bash
/usr/bin/time -p curl -s -o /dev/null https://example.com
```
**Output**
```
real 0.11
user 0.01
sys 0.00
```
`/usr/bin/time -p` is not part of curl: it measures any command. `real` is the total time in seconds.

---

## Cheat sheet

| Option | What it does | Used in |
|---|---|---|
| `-i` | show headers and body | 02_02, 02_04 |
| `-I` | only headers (`HEAD` request) | 02_02 |
| `-v` | the whole conversation (`*`, `>`, `<`) | 02_03, 02_04, 02_05, 02_06 |
| `-s` / `-S` | hide the progress bar / still show errors | everywhere |
| `-o file` / `-o /dev/null` | save / throw away the body | everywhere |
| `2>&1 \| grep` | filter the lines of `-v` | 02_03, 02_04, 02_05, 02_06 |
| `-w '...%{var}...'` | print variables after the transfer | 02_03, 02_05, 02_06 |
| `-H 'Name: value'` | add a header | (not used in the labs) |
| `-L`, `--max-redirs N` | follow redirects (at most N) | 02_02 |
| `-c file` / `-b file`, `-b 'name=value'` | save / send cookies (from a file or by hand) | 02_04 |
| `-x host:port` | use a proxy | 02_03 |
| `-D -` | print the response headers (also with `-o /dev/null`) | 02_03 |
| `'...[1-3]'`, `'...{a,b}'` | many URLs in one command | 02_05, 02_06 |
| `--http1.0`, `--http1.1`, `--http2` | choose the HTTP version | 02_05, 02_06 |
| `--http2-prior-knowledge` | HTTP/2 without asking first (explained in 02_06) | 02_06 |
| `--parallel`, `--parallel-max N` | requests at the same time (at most N) | 02_06 |
| `/usr/bin/time -p` | total time of a command | 02_05 |
