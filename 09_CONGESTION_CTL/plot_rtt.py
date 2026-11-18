#!/usr/bin/env python
# Plot the RTT of one or more CSV files written by cwnd_client.py
# RTT above the cable delay = time spent waiting in the router queue

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")    # no window: only write the image file
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("files", nargs="+", help="CSV files, e.g. cubic.csv bbr.csv")
parser.add_argument("--out", default="rtt.png", help="image file (.png, .svg, .pdf)")
parser.add_argument("--delay", type=float, default=0,
                    help="cable delay in ms, drawn as a line: the DELAY of emulate_channel.sh (0 = no line)")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

# read all the files
curves = []
for name in args.files:
    times = []
    rtt = []
    rows = csv.DictReader(open(name))
    if "rtt" not in rows.fieldnames:
        sys.exit("%s has no 'rtt' column: run cwnd_client.py again to record it" % name)
    for row in rows:
        times.append(float(row["time"]))
        rtt.append(float(row["rtt"]))
    curves.append([name, times, rtt])

# time 0 = the first sample of all the files (absolute time: clients started later appear later)
t0 = min(curve[1][0] for curve in curves)

styles = ["-", "--", ":", "-."]    # one line style per file, black and white
plt.figure(figsize=(9, 4))
for i, curve in enumerate(curves):
    name, times, rtt = curve
    t = [x - t0 for x in times]
    label = os.path.basename(name).replace(".csv", "")
    print("%s: average RTT %.1f ms (min %.1f, max %.1f)" % (label, sum(rtt) / len(rtt), min(rtt), max(rtt)))
    plt.plot(t, rtt, styles[i % 4], color="black", linewidth=1, label=label)

if args.delay > 0:
    plt.axhline(args.delay, color="0.6", linewidth=1)
    plt.text(0.01, args.delay, "cable %g ms (empty queue)" % args.delay, va="bottom", color="0.4",
             transform=plt.gca().get_yaxis_transform())    # x in axes units, y in ms

plt.xlabel("time (s)")
plt.ylabel("RTT (ms)")
plt.ylim(bottom=0)
plt.grid(color="0.85")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig(args.out, dpi=150)
print("plot saved in", args.out)
