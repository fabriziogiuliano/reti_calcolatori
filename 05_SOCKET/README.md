# UDP sockets with ncat (Linux / macOS)

Reference: Kurose & Ross, *Computer Networking*, Ch. 2 (Sec. 2.7) and Ch. 3 (Sec. 3.3)

Install: `sudo apt install ncat tcpdump` (macOS: `brew install nmap`, ncat is part of Nmap; tcpdump is already installed)

Windows: run everything inside WSL (Ubuntu), as on Linux.

A socket is identified by **IP address + port**. Here we open a UDP server and a UDP client with `ncat`, then look at the sockets from the operating system.

### The options used in this lab

| Option | What it does | First used in |
|---|---|---|
| `ncat -u` | use UDP instead of TCP | 1 |
| `ncat -l` | listen: act as a server and wait on a port | 1 |
| `ncat -k` | keep open: the server keeps accepting new clients, not only the first one | 1 |
| `lsof -i UDP:8888` | list the open sockets that use UDP port 8888 | 2 |
| `lsof -n` | show IP addresses, do not translate them into names | 2 |
| `lsof -P` | show port numbers, do not translate them into service names | 2 |
| `tcpdump -i lo` | capture on the loopback interface (`127.0.0.1`); on macOS it is called `lo0` | 3 |
| `tcpdump -n` | show IP addresses and port numbers, do not translate them into names | 3 |
| `tcpdump -A` | also print the content of each packet as text | 3 |
| `udp port 8888` | filter: capture only UDP packets to or from port 8888 | 3 |

Online: [ncat guide](https://nmap.org/ncat/guide/), [lsof manual](https://man7.org/linux/man-pages/man8/lsof.8.html), [tcpdump manual](https://www.tcpdump.org/manpages/tcpdump.1.html) (or `man ncat`, `man lsof`, `man tcpdump` in the terminal).

---

## 1. Open a UDP server and a UDP client

> The server opens a socket on a fixed port and waits. The client opens a socket on a random port and sends to the server.

### Command

In the left pane, start the server: it waits on UDP port 8888.

```bash
ncat -u -l 8888
```

### Command

In the right pane, start the client: it sends to port 8888 on this machine (`127.0.0.1`).

```bash
ncat -u 127.0.0.1 8888
```

Type `hello` in the client and press Enter.

**Server output**
```
hello
```
Every line you type is sent as **one UDP datagram**. No connection is opened before: the first datagram already carries the data.

Now type `hi` in the server and press Enter: it appears in the client. The server learned the client's address (IP + port) from the first datagram it received.

### Command

Close the client (Ctrl+C), start it again and type `hello`.

```bash
ncat -u 127.0.0.1 8888
```
**Client output**
```
hello
Ncat: Connection refused.
```
The server is still running, but it refuses the new client. At the first datagram the server tied its socket to the first client (IP + port). The new client starts from a different random port, so no socket accepts its datagrams and the system answers with an ICMP "port unreachable" message.

### Command

Stop the server (Ctrl+C) and start it again with `-k` (keep open).

```bash
ncat -u -l -k 8888
```

<details>
<summary>Troubleshooting: "UDP mode does not support the -k or --keep-open options"</summary>

Old versions of ncat do not accept `-k` in UDP mode. Ubuntu (and so WSL) installs ncat 7.80, which stops with:
```
Ncat: UDP mode does not support the -k or --keep-open options, except with --exec or --sh-exec. QUITTING.
```
Check your version with `ncat --version`: on macOS Homebrew installs a recent one (7.97), where `-k` works.

Workaround: as UDP server use `server-udp.py` (in [05_SOCKET](./)) instead of `ncat -u -l -k 8888`. It listens on the same port 8888 and accepts datagrams from any client, and it prints each one with the address of the sender.
</details>

Now you can close and reopen the client as many times as you want: every new client reaches the server.

---

## 2. See the sockets opened by the system

> The operating system keeps a list of all the open sockets. `lsof` prints it.

### Command

In a third pane, with the server running (`ncat -u -l -k 8888`) and the client **not yet started**:

```bash
lsof -nP -i UDP:8888
```
**Expected output**
```
COMMAND   PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
ncat    17333 fabrizio    3u  IPv6 0x57e700733c2e0c99      0t0  UDP *:8888
ncat    17333 fabrizio    4u  IPv4 0xc9f49cf35630848b      0t0  UDP *:8888
```
- `COMMAND` / `PID`: the program that owns the socket.
- `NAME`: `*:8888` means "any local address, port 8888", so the server is waiting for anyone. ncat opens two sockets: one for IPv4, one for IPv6.

### Command

Start the client, send one line, and run the same command again.

```bash
lsof -nP -i UDP:8888
```
**Expected output**
```
COMMAND   PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
ncat    17333 fabrizio    3u  IPv6 0x57e700733c2e0c99      0t0  UDP *:8888
ncat    17333 fabrizio    4u  IPv4 0xc9f49cf35630848b      0t0  UDP 127.0.0.1:8888->127.0.0.1:62819
ncat    17333 fabrizio    5u  IPv4 0x2a027442b84d7498      0t0  UDP *:8888
ncat    17340 fabrizio    3u  IPv4 0xf27059de625bfe26      0t0  UDP 127.0.0.1:62819->127.0.0.1:8888
```
- server (PID 17333), line 2: its socket is now tied to the client: local port `8888`, remote port `62819`.
- server (PID 17333), line 3: a **new** socket `*:8888`, opened thanks to `-k` and waiting for the next client. Without `-k` this line is missing: that is why the second client got `Connection refused` (section 1).
- client (PID 17340): local port `62819`, chosen at random by the system, remote port `8888`.

Each line is `local address -> remote address`: the server socket and the client socket are the two ends of the same exchange.

### Command

Stop the server (Ctrl+C) and run the command once more.

```bash
lsof -nP -i UDP:8888
```
**Expected output**: nothing. The socket is closed together with the program.

*Linux note:* `ss -ulnp` lists all the UDP sockets in listening state, with the program that owns them ([ss manual](https://man7.org/linux/man-pages/man8/ss.8.html)).

---

## 3. See the datagrams with tcpdump

> `tcpdump` captures the packets that pass on a network interface and prints one line per packet.

### Command

Start the server again (`ncat -u -l -k 8888`). In a third pane, start the capture (on macOS write `lo0` instead of `lo`):

```bash
sudo tcpdump -i lo -n -A udp port 8888
```
Start the client, type `hello` and press Enter.

**tcpdump output**
```
listening on lo0, link-type NULL (BSD loopback), snapshot length 524288 bytes
16:54:52.557863 IP 127.0.0.1.52290 > 127.0.0.1.8888: UDP, length 6
E..".T..@............B"....!hello
```
- `127.0.0.1.52290 > 127.0.0.1.8888`: source address.port `>` destination address.port. `52290` is the client's random port, the same one `lsof` shows.
- `UDP, length 6`: the payload is 6 bytes, `hello` plus the Enter (newline).
- The second line is the packet printed as text: the IP and UDP headers are unreadable dots and symbols, the payload `hello` is at the end.

One line typed = one datagram captured. Stop the capture with Ctrl+C.

