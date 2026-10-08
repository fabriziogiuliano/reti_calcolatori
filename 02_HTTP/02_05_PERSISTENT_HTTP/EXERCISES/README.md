# Exercise 02.5: a slower network

**Goal:** check the formulas of persistent and non-persistent HTTP with a different RTT.

## Task

1. In `server.py`, change the RTT from 0.5 s to 1 s.
2. Before running anything, write down: with 3 objects, how long does each object take, with HTTP/1.0 and with HTTP/1.1? And in total?
3. Restart the server and measure with the commands of the README (Steps 2 and 3).

## What you need

- The variable `RTT` at the top of `server.py`.
- The formulas in the Concepts of the README: non-persistent N × 2 RTT, persistent 2 RTT + (N − 1) × 1 RTT.
- The commands of Steps 2 and 3 (`--http1.0` and `--http1.1`, `[1-3]`).

## Check

Your prediction and the measure agree. At the end, put `RTT = 0.5` back.

<details>
<summary>Solution</summary>

```python
RTT = 1
```
Prediction: non-persistent 2 s + 2 s + 2 s = 6 s; persistent 2 s + 1 s + 1 s = 4 s.

Measure:
```bash
curl --http1.0 -s -w 'time: %{time_total}s\n' 'http://localhost:8000/[1-3]'
curl --http1.1 -s -w 'time: %{time_total}s\n' 'http://localhost:8000/[1-3]'
```
```
time: 2.008651s     <- HTTP/1.0, every object 2 RTT
time: 2.011202s
time: 2.007223s

time: 2.008982s     <- HTTP/1.1, the first object 2 RTT
time: 1.006353s     <- the next ones 1 RTT
time: 1.002659s
```
(The `You asked for /...` lines are left out.)
</details>
