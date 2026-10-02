# Writes in front of every line it receives how many seconds have passed since it started.
# Used as:  curl ... | python arrival.py   -> "after 3.0 s   <line printed by curl>"
import sys
import time

t0 = time.time()
for line in sys.stdin:
    print(f'after {time.time() - t0:4.1f} s   {line}', end='', flush=True)
