# 02.4 Cookies: a shopping cart

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.2.4)

## Concepts

1. HTTP is **stateless**: the server does not remember you from one request to the next.
2. A **cookie** is a number the server gives you. You show it in every request, and the server recognizes you.
3. Like a **cloakroom ticket**: you keep only the number, the coat stays at the cloakroom. Your PC keeps only `id=1678`; the cart stays on the server.
4. The 4 components of cookies:

| Component | In this lab |
|---|---|
| `Set-Cookie` header in the **response** | the server gives you `id=1678` |
| `Cookie` header in the **request** | you show `id=1678` again |
| a **file** on the client | `cookies.txt` (in the browser: its cookie storage) |
| a **database** on the server | the `carts` dictionary in `cart_server.py` |

5. A cookie is a **bearer ticket**: whoever shows it *is* you. A safe cookie is **impossible to guess**, **hidden from JavaScript**, and travels **only encrypted**.

## Files

| File | What it is |
|---|---|
| `cart_server.py` | A tiny shop, port **8000**. `/add?item=book` adds an item to your cart, `/cart` shows your cart |

Use two tmux panes: the **server** on the left, the **client commands** on the right. Start `cart_server.py` in the left pane. For every request it prints the `Cookie` header it received.

---

## Step 1. First purchase, without a cookie

**What it does:** `-i` also prints the response headers.

> All curl options are explained in the [official curl manual](https://curl.se/docs/manpage.html) (or `man curl` in the terminal). A friendly guide with examples: [everything curl](https://everything.curl.dev/).

```bash
curl -i 'http://localhost:8000/add?item=book'
```
**Expected output**
```
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.11.17
Date: Fri, 02 Oct 2026 15:38:37 GMT
Set-Cookie: id=1678

Customer 1678. Your cart: ['book']
```
`Set-Cookie: id=1678`: the server gives you your number. Server log: `Cookie received: None`.

## Step 2. Second purchase, showing the cookie by hand

**What it does:** `-b 'id=1678'` puts the header `Cookie: id=1678` in the request: we show our number by hand.

```bash
curl -b 'id=1678' 'http://localhost:8000/add?item=pen'
```
**Expected output**
```
Customer 1678. Your cart: ['book', 'pen']
```
The server recognized you. Server log: `Cookie received: id=1678`.

## Step 3. Look at the cart without the cookie

```bash
curl http://localhost:8000/cart
```
**Expected output**
```
Customer 1679. Your cart: []
```
Without the cookie you are a **new customer**. Your cart is not lost: it is still on the server under `1678`. You just did not show your number.

## Step 4. Let curl remember the cookie

Typing the number by hand is boring. curl can do it, like a browser:

| Option | What it does |
|---|---|
| `-c cookies.txt` | **after** the response: save the cookies received (`Set-Cookie`) in the file |
| `-b cookies.txt` | **before** the request: send the cookies in the file (`Cookie`). The same option as Step 2, now with a file instead of the cookie written by hand |
| `-v` | **verbose**: show the whole exchange. Lines with `>` go **from client to server**, lines with `<` go **from server to client** |
| `-s` | **silent**: hide the progress bar |
| `2>&1` | `-v` writes on the error channel (stderr): this sends it to the normal output, so that `grep` can read it |
| `grep -iE '...'` | keep only the lines that match (`-i`: ignore upper/lower case, `-E`: `\|` means "or") |

**First purchase:**
```bash
curl -sv -c cookies.txt -b cookies.txt 'http://localhost:8000/add?item=apple' 2>&1 | grep -iE '^(> GET|> cookie|< HTTP|< set-cookie)|^Customer'
```
**Expected output**
```
> GET /add?item=apple HTTP/1.1
< HTTP/1.0 200 OK
< Set-Cookie: id=1680
Customer 1680. Your cart: ['apple']
```
Request: **no** `Cookie`. Response: `Set-Cookie`.

**Second purchase** (same command, different item):
```bash
curl -sv -c cookies.txt -b cookies.txt 'http://localhost:8000/add?item=kiwi' 2>&1 | grep -iE '^(> GET|> cookie|< HTTP|< set-cookie)|^Customer'
```
**Expected output**
```
> GET /add?item=kiwi HTTP/1.1
> Cookie: id=1680
< HTTP/1.0 200 OK
Customer 1680. Your cart: ['apple', 'kiwi']
```
Request: `Cookie: id=1680`, taken from the file. Response: **no** `Set-Cookie`, the server already knows you.

> `Set-Cookie`: server → client, **once**. `Cookie`: client → server, **every time**.

## Step 5. Look at the file

```bash
cat cookies.txt
```
**Expected output** (last line)
```
localhost	FALSE	/	FALSE	0	id	1680
```
Only the number. The cart is not here: it is on the server.

## Step 6. The same with the browser

Open these addresses one after the other:

1. `http://localhost:8000/add?item=book`
2. `http://localhost:8000/add?item=pen`
3. `http://localhost:8000/cart`

Same customer number, the cart grows: the browser sends the cookie by itself, like `-b`.

See the cookie in the developer tools (`Cmd+Option+I`): Firefox *Storage → Cookies*, Chrome *Application → Cookies*. Delete it and reload `/cart`: you are a new customer.

Look at the server log: the browser may send **other cookies too**, all in one line, e.g. `Cookie received: _xsrf=abc; id=1681`. A browser sends **all** the cookies it has for that site, every time.

---

## Part B. Is it safe?

## Step 7. Steal a cart by guessing the number

In the browser your cookie is, for example, `id=1681`. Then who are `1680`, `1679`, `1678`...? Show **somebody else's** number:

```bash
curl -b 'id=1678' http://localhost:8000/cart
```
**Expected output**
```
Customer 1678. Your cart: ['book', 'pen']
```
The cart of Steps 1-2: not yours. Now change it:
```bash
curl -b 'id=1678' 'http://localhost:8000/add?item=tv'
```
**Expected output**
```
Customer 1678. Your cart: ['book', 'pen', 'tv']
```
The numbers are **consecutive**: if you know one, you know them all. The server does not check **who** you are, it only reads the number.

## Step 8. Make the cookie safe: a mini-guide

Open `cart_server.py` in an editor and make the changes below. After every change stop the server (`Ctrl+c`) and start it again.

**Change 1. A random id** (against guessing)

At the top, add:
```python
import secrets
```
Where a new customer gets a number, replace the two lines with one:
```diff
-            user = str(next_id)
-            next_id += 1
+            user = secrets.token_urlsafe(16)    # 16 random bytes = 128 bits
```
[`secrets`](https://docs.python.org/3/library/secrets.html) makes random values that cannot be predicted. Repeat Step 1, then the attack of Step 7:
```
Set-Cookie: id=_D8QIBf758e7t5rw6exhig
...
Customer UX4HNVzfjGkozzy-x07h4g. Your cart: []
```
`1678` is now an unknown number: you are a **new customer**, with an empty cart. And your own id says nothing about the others: there are 2^128 possible ids, nobody can try them all.

**Change 2. `HttpOnly` and `SameSite`** (against theft inside the browser)

Add two **attributes** to the cookie:
```diff
-            self.send_header('Set-Cookie', f'id={user}')
+            self.send_header('Set-Cookie', f'id={user}; HttpOnly; SameSite=Lax')
```
| Attribute | What the browser does | Protects from |
|---|---|---|
| `HttpOnly` | sends the cookie to the server, but **JavaScript cannot read it** | a script injected in the page that reads `document.cookie` and sends it to an attacker (**XSS**) |
| `SameSite=Lax` | does **not** attach the cookie to requests started by **another site** (an image, a hidden form) | another site that makes you use your cookie without knowing it, e.g. `<img src="http://localhost:8000/add?item=tv">` (**CSRF**) |

Check in the browser (Step 6): in the developer tools the `id` cookie has *HttpOnly* ✓ and *SameSite* `Lax`. In the *Console* type `document.cookie`: `id` is **not** there.

curl ignores both attributes: it runs no JavaScript and `-b` always sends the cookie. The attributes are defined by the cookie standard ([RFC 6265](https://www.rfc-editor.org/rfc/rfc6265)), but it is the **browser** that applies them. The random id instead is a choice of the **application**: for HTTP, `1678` and `_D8QIBf758e7t5rw6exhig` are the same thing. Full list of attributes: [Set-Cookie on MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).

**Change 3. `Secure`** (against reading the traffic): not here

With http the cookie travels **in clear**: whoever sees the traffic (Wireshark, the Wi-Fi of a bar) copies it and *is* you, random or not. The attribute `Secure` tells the browser: send this cookie **only over https**. It needs TLS, so we stop here.

> **How** TLS encrypts the traffic is a topic of the security chapter: Kurose & Ross, Ch. 8 (Sec. 8.6).

At the end, restore the original server: `git checkout cart_server.py`.

---

## Questions

**Q1.** Stop the server and start it again. Then run the command of Step 2 again. What happens to the book, and why?

**Q2.** A classmate reads your number (for example `1680`). What can they do with it?

---

## Solutions

<details>
<summary>Q1</summary>

The answer is `Customer 1678. Your cart: ['pen']`, with a new `Set-Cookie: id=1678`: the book is gone. The database is a dictionary in memory: restarting the server deletes it. You still have your ticket, but the cloakroom was emptied. (The number is again 1678 only because the counter restarts from 1678 too.)
</details>

<details>
<summary>Q2</summary>

They can send `Cookie: id=1680` and the server thinks they are you: they see and change your cart. Whoever has the ticket gets the coat. And with consecutive numbers they do not even need to read yours: they can guess it (Step 7). A random id stops the guessing (Step 8), but with plain http anybody who can see the traffic can still read the cookie: only https (`Secure`) stops that.
</details>
