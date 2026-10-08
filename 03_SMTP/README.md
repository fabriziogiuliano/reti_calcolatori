# 03 SMTP: sending e-mail by hand

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.3, Electronic Mail in the Internet)

## Concepts

1. E-mail has three actors: the user agent (the mail program of Alice), the mail servers, and SMTP, the protocol that moves the mail from one server to the next.
2. SMTP runs on TCP (port 25 on the Internet; our lab server uses port 2525). Like HTTP it is text: the client sends short commands, the server answers with a number and a message.
3. The conversation always has the same steps: `EHLO` (hello), `MAIL FROM` (sender), `RCPT TO` (receiver), `DATA` (the message), `.` (end of the message), `QUIT`.
4. The message itself has header lines (`From:`, `To:`, `Subject:`), an empty line, then the body.
5. SMTP is a push protocol: the client pushes the mail to the server. HTTP is a pull protocol: the client pulls a page from the server.

## Files

| File | What it is |
|---|---|
| `smtp_server.py` | A local mail server, port 2525. It does not deliver anything: it prints every mail it receives, split into envelope and message |
| `smtp_client.py` | A mail client in Python: it sends one mail and shows every command and reply |
| `mail.txt` | A ready mail, used with curl |

Our server uses the library aiosmtpd ([documentation](https://aiosmtpd.aio-libs.org/)), installed by `setup_env.sh`. We use it as a black box.

Use two tmux panes: the server on the left, the client on the right. Start `smtp_server.py` in the left pane. It prints:
```
Mail server on 127.0.0.1:2525 ...  (Ctrl+c to stop)
```

---

## Part A. Send a mail by hand

You play the user agent: you open a TCP connection to the server and type the SMTP commands yourself.

### Step 1. Connect

`ncat` opens a TCP connection to the server and lets you type. `-C` turns every Enter into `\r\n`, the line ending SMTP requires (as in HTTP).

```bash
ncat -C 127.0.0.1 2525
```
**Server answers**
```
220 mail.lab Python SMTP 1.4.6
```
`220` means the server is ready.

### Step 2. Say hello

**You type**
```
EHLO my-pc
```
**Server answers**
```
250-mail.lab
250-SIZE 33554432
250-8BITMIME
250-SMTPUTF8
250 HELP
```
`250` means OK. The other lines list the extra features the server supports: you can ignore them.

### Step 3. The sender

**You type**
```
MAIL FROM:<alice@unipa.it>
```
**Server answers**
```
250 OK
```

### Step 4. The receiver

**You type**
```
RCPT TO:<bob@example.com>
```
**Server answers**
```
250 OK
```

### Step 5. Start the message

**You type**
```
DATA
```
**Server answers**
```
354 End data with <CR><LF>.<CR><LF>
```
`354` means go on: write the message and end it with a line that contains only a dot.

### Step 6. Write the message and end it

**You type** (headers, an empty line, the body, a line with only `.`)
```
From: Alice <alice@unipa.it>
To: Bob <bob@example.com>
Subject: Hello

Hi Bob,
this mail was typed by hand.
.
```
**Server answers**
```
250 OK: message accepted
```
**Server log:**
```
============================================================
ENVELOPE (from the SMTP commands)
  MAIL FROM: alice@unipa.it
  RCPT TO:   bob@example.com
MESSAGE (after DATA: headers, empty line, body)
From: Alice <alice@unipa.it>
To: Bob <bob@example.com>
Subject: Hello

Hi Bob,
this mail was typed by hand.
```

### Step 7. Close

**You type**
```
QUIT
```
**Server answers**
```
221 Bye
```

### The whole conversation

| You type | Server answers | Meaning |
|---|---|---|
| (connect) | `220` | server ready |
| `EHLO my-pc` | `250` | hello accepted |
| `MAIL FROM:<...>` | `250` | sender accepted |
| `RCPT TO:<...>` | `250` | receiver accepted |
| `DATA` | `354` | write the message |
| headers, empty line, body, `.` | `250` | message accepted |
| `QUIT` | `221` | connection closed |

The reply codes have classes, as in HTTP: `2xx` OK, `3xx` go on, `4xx` and `5xx` error.

---

## Part B. Envelope and letter

The server log has two parts:
- the envelope: `MAIL FROM` and `RCPT TO`, the SMTP commands. The mail servers use them to deliver the mail;
- the letter: the `From:` and `To:` header lines inside the message. The mail program of Bob shows them on screen.

Nobody checks that they are the same.

### Step 8. A fake sender

Connect again (`ncat -C 127.0.0.1 2525`) and type:
```
EHLO my-pc
MAIL FROM:<student@unipa.it>
RCPT TO:<bob@example.com>
DATA
From: The Rector <rector@unipa.it>
To: Bob <bob@example.com>
Subject: You passed the exam

Congratulations!
.
```
**Server log:**
```
ENVELOPE (from the SMTP commands)
  MAIL FROM: student@unipa.it
  RCPT TO:   bob@example.com
MESSAGE (after DATA: headers, empty line, body)
From: The Rector <rector@unipa.it>
To: Bob <bob@example.com>
Subject: You passed the exam

Congratulations!
```
The envelope says `student`, but Bob's mail program shows "From: The Rector". This is how spam and phishing fake the sender.

### Step 9. Two mails on the same connection

Do not type `QUIT`: after the `250` of the first mail, start a second one on the same connection:
```
MAIL FROM:<student@unipa.it>
RCPT TO:<carol@example.com>
DATA
Subject: Second mail

Same connection, second mail.
.
QUIT
```
The server log shows a second mail. SMTP uses persistent connections: many mails, one TCP connection (as persistent HTTP in `02_05`).

---

## Part C. Let a program do it

### Step 10. A Python client

Run `smtp_client.py` in the right pane. `set_debuglevel(1)` prints what the program sends (`send:`) and receives (`reply:`). Only the important lines:

**Client output**
```
send: 'ehlo my-pc\r\n'
reply: b'250-mail.lab\r\n'
...
send: 'mail FROM:<alice@unipa.it> size=128\r\n'
reply: b'250 OK\r\n'
send: 'rcpt TO:<bob@example.com>\r\n'
reply: b'250 OK\r\n'
send: 'data\r\n'
reply: b'354 End data with <CR><LF>.<CR><LF>\r\n'
send: b'From: Alice <alice@unipa.it>\r\nTo: Bob <bob@example.com>\r\nSubject: Hello from Python\r\n\r\nHi Bob,\r\nthis mail was sent by smtplib.\r\n.\r\n'
reply: b'250 OK: message accepted\r\n'
send: 'QUIT\r\n'
reply: b'221 Bye\r\n'
```
The same commands you typed in Part A, in the same order. Look at the end of the message: `\r\n.\r\n`, the line with only a dot. Python library: [smtplib](https://docs.python.org/3/library/smtplib.html).

### Step 11. curl

curl speaks SMTP too ([SMTP in everything curl](https://everything.curl.dev/usingcurl/smtp.html)):

| Option | What it does |
|---|---|
| `smtp://127.0.0.1:2525` | the mail server |
| `--mail-from` | the sender: `MAIL FROM` |
| `--mail-rcpt` | the receiver: `RCPT TO` |
| `-T mail.txt` | the message to send after `DATA` (headers, empty line, body) |
| `-v ... 2>&1 \| grep -E '^[<>]'` | show only what is sent (`>`) and received (`<`) |

```bash
curl -s smtp://127.0.0.1:2525 --mail-from alice@unipa.it --mail-rcpt bob@example.com -T mail.txt -v 2>&1 | grep -E '^[<>]'
```
**Client output**
```
< 220 mail.lab Python SMTP 1.4.6
> EHLO mail.txt
< 250-mail.lab
< 250-SIZE 33554432
< 250-8BITMIME
< 250-SMTPUTF8
< 250 HELP
> MAIL FROM:<alice@unipa.it> SIZE=117
< 250 OK
> RCPT TO:<bob@example.com>
< 250 OK
> DATA
< 354 End data with <CR><LF>.<CR><LF>
< 250 OK: message accepted
```
Again the same conversation. (curl writes the file name after `EHLO`: the server does not care.)

---

## Questions

**Q1.** SMTP and HTTP both send text commands on TCP and answer with numbered codes. What is the main difference in who sends the data to whom?

**Q2.** The message ends with a line containing only `.`. What would go wrong if the body of the mail had a line with only a dot?

**Q3.** After Step 8, how could Bob's mail server find out that `student@unipa.it` is not allowed to send mail as `rector@unipa.it`?

**Q4.** Why does Alice send her mail to her own mail server, and not directly to Bob's computer?

---

## Solutions

<details>
<summary>Q1</summary>

SMTP is a push protocol: the client opens the connection and sends the mail to the server. HTTP is a pull protocol: the client opens the connection and asks for a page, the server sends it.
</details>

<details>
<summary>Q2</summary>

The server would think the message is over at that line. To avoid it, the client adds an extra dot at the start of any body line that begins with a dot (`.` becomes `..`), and the server removes it.
</details>

<details>
<summary>Q3</summary>

SMTP alone cannot: it trusts what the client writes. Extra checks were added later. For example SPF: the domain `unipa.it` publishes in the DNS (a TXT record) the list of servers allowed to send its mail, and Bob's server checks it. We will see TXT records in the DNS lab.
</details>

<details>
<summary>Q4</summary>

Bob's computer may be switched off or offline. Mail servers are always on: Alice's server keeps the mail in a queue and retries until Bob's server accepts it; Bob reads it later from his server.
</details>
