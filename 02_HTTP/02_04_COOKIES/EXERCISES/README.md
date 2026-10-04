# Exercise 02.4: change the customer numbers

**Goal:** see where the server creates the cookie value.

## Task

1. In `cart_server.py`, make the customer numbers start from **1000** instead of 1678.
2. Restart the server and repeat Step 1 of the README.
3. Which number does the server give you in `Set-Cookie`?

## What you need

- The variable `next_id` at the top of `cart_server.py`.
- The command of the README, Step 1 (`curl -i`).

## Check

`Set-Cookie: id=1000`. At the end, put `1678` back.

<details>
<summary>Solution</summary>

```python
next_id = 1000
```
```bash
curl -i 'http://localhost:8000/add?item=book'
```
The interesting lines:
```
Set-Cookie: id=1000
Customer 1000. Your cart: ['book']
```
The value of the cookie is decided **by the server**: the client only keeps it and sends it back.
</details>
