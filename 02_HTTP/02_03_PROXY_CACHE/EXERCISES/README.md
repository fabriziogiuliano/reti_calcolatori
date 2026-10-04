# Exercise 02.3: a new object in the cache

**Goal:** put a new file on the origin server and see it go through the proxy cache.

## Task

1. Create a file `hello.txt` in the `www/` folder, with one line of text.
2. With the origin server and the proxy running, download `http://localhost:8000/hello.txt` **through the proxy**, twice.
3. Which download is `MISS`, which is `HIT`? How long does each one take?

## What you need

- A text file: any editor, or `echo "Hello from the origin server" > www/hello.txt`.
- The command of the README, Step 4 (`-x localhost:8080`, `-D -`, `-w`): change only the file name.

## Check

The first time `MISS` (about 2 s), the second time `HIT` (a few ms). The origin server log shows **one** request for `/hello.txt`.

<details>
<summary>Solution</summary>

```bash
echo "Hello from the origin server" > www/hello.txt
curl -s -D - -o /dev/null -w 'time: %{time_total}s\n' -x localhost:8080 http://localhost:8000/hello.txt
```
Run the command twice. The interesting lines:
```
X-Cache: MISS
time: 2.016081s
```
```
X-Cache: HIT
time: 0.000736s
```
</details>
