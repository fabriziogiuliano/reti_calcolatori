# Exercise 03: change the receiver

**Goal:** send a mail to another person with the Python client, and find out where the receiver is written.

## Task

1. In `smtp_client.py`, send the mail to Carol (`carol@example.com`) instead of Bob, with the subject "Exam tomorrow".
2. Run the client and look at the server log: is Carol in the envelope and in the letter?

## What you need

- `smtp_client.py`: the message (the `To:` and `Subject:` lines) and the `sendmail(...)` line.
- README, Part B: envelope (`RCPT TO`) and letter (`To:`).

## Check

The server log shows `RCPT TO: carol@example.com` and `To: Carol <carol@example.com>`, `Subject: Exam tomorrow`.

<details>
<summary>Solution</summary>

The receiver is written in two places: change both.
```python
To: Carol <carol@example.com>              # the letter (header line)
Subject: Exam tomorrow
...
server.sendmail('alice@unipa.it', ['carol@example.com'], message)   # the envelope (RCPT TO)
```
Server log:
```
ENVELOPE (from the SMTP commands)
  MAIL FROM: alice@unipa.it
  RCPT TO:   carol@example.com
MESSAGE (after DATA: headers, empty line, body)
From: Alice <alice@unipa.it>
To: Carol <carol@example.com>
Subject: Exam tomorrow
```
If you change only the `To:` line, the mail still goes to Bob (envelope), but it shows "To: Carol": envelope and letter are independent.
</details>
