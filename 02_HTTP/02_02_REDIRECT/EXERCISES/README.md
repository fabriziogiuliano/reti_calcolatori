# Exercise 02.2: your own redirect chain

**Goal:** add a new redirect chain to the server and follow it.

## Task

1. In `redirect_server.py`, add two paths to the `ROUTES` dictionary:
   - `/x` answers 301 and sends to `/y`;
   - `/y` answers 302 and sends to `/c`.
2. Restart the server.
3. Follow the chain from `/x` with curl.

## What you need

- The `ROUTES` dictionary of `redirect_server.py`: copy one of the existing lines and change it.
- `curl -iL` (README, Step 7): shows every response of the chain.

## Check

You see three responses: `301`, `302`, `200`, and at the end `<h1>You made it!</h1>`.

<details>
<summary>Solution</summary>

The two new lines in `ROUTES`:
```python
    '/x':     (301, '/y'),
    '/y':     (302, '/c'),
```
```bash
curl -iL http://localhost:8000/x
```
Only the important lines:
```
HTTP/1.0 301 Moved Permanently
Location: /y
HTTP/1.0 302 Found
Location: /c
HTTP/1.0 200 OK
<h1>You made it!</h1>
```
</details>
