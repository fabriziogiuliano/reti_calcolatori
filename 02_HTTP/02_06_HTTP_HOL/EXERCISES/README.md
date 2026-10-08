# Exercise 02.6: a fourth object

**Goal:** predict Head-of-Line blocking with one more object.

## Task

1. In `server.py`, add a medium object to `SIZES` that takes 2 s.
2. Before running anything, fill this table: after how many seconds does each object arrive?

   | | `/large` | `/medium` | `/small` | `/tiny` | Connections |
   |---|---|---|---|---|---|
   | Step 1. HTTP/1.1 | | | | | |
   | Step 2. HTTP/1.1 `--parallel` | | | | | |
   | Step 3. HTTP/1.1 `--parallel --parallel-max 2` | | | | | |
   | Step 4. HTTP/2 `--parallel` | | | | | |

3. Restart the server and check with the commands of the README, asking for `'http://localhost:8000/{large,medium,small,tiny}'`.

## What you need

- The `SIZES` dictionary of `server.py`: copy one line and change it.
- The commands of Steps 1 to 4: change only the list of objects in the URL.

## Check

Your table and the `after ... s` of `arrival.py` agree. At the end, remove `/medium`.

<details>
<summary>Solution</summary>

The new line in `SIZES`:
```python
    '/medium': 2,                      # a medium file (a photo)
```
| | `/large` | `/medium` | `/small` | `/tiny` | Connections |
|---|---|---|---|---|---|
| Step 1. HTTP/1.1 | 3 s | 5 s | 6 s | 6 s | 1 |
| Step 2. HTTP/1.1 `--parallel` | 3 s | 2 s | 1 s | 0 s | 4 |
| Step 3. HTTP/1.1 `--parallel --parallel-max 2` | 3 s | 2 s | 3 s | 3 s | 2 |
| Step 4. HTTP/2 `--parallel` | 3 s | 2 s | 1 s | 0 s | 1 |

Step 1: one queue, every object waits for all the ones before it.
Step 3: `/large` and `/medium` take the 2 connections; `/small` starts when `/medium` ends (2 s) and arrives at 3 s; `/tiny` waits behind `/small` and arrives at 3 s too.
</details>
