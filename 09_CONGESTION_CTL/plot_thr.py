#!/usr/bin/env python
# Plot the throughput of one or more CSV files written by cwnd_client.py
# throughput = bytes delivered in the last --window seconds / --window

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")    # no window: only write the image file
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("files", nargs="+", help="CSV files, e.g. reno.csv cubic.csv")
parser.add_argument("--out", default="thr.png", help="image file (.png, .svg, .pdf)")
parser.add_argument("--window", type=float, default=0.5, help="seconds over which the throughput is averaged")
parser.add_argument("--link", type=float, default=0,
                    help="link capacity in Mbit/s, drawn as a line: the RATE of emulate_channel.sh (0 = no line)")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

# read all the files
curves = []
for name in args.files:
    times = []
    nbytes = []
    rows = csv.DictReader(open(name))
    if "bytes" not in rows.fieldnames:
        sys.exit("%s has no 'bytes' column: run cwnd_client.py again to record it" % name)
    for row in rows:
        times.append(float(row["time"]))
        nbytes.append(int(row["bytes"]))
    curves.append([name, times, nbytes])

# time 0 = the first sample of all the files (absolute time: clients started later appear later)
t0 = min(curve[1][0] for curve in curves)

styles = ["-", "--", ":", "-."]    # one line style per file, black and white
plt.figure(figsize=(9, 4))
for i, curve in enumerate(curves):
    name, times, nbytes = curve

    # for each sample, go back to the first sample at least --window seconds older
    t = []
    thr = []
    j = 0
    for k in range(len(times)):
        while times[k] - times[j + 1] >= args.window:
            j += 1
        if times[k] - times[j] < args.window:    # not enough history yet
            continue
        t.append(times[k] - t0)
        thr.append((nbytes[k] - nbytes[j]) * 8 / (times[k] - times[j]) / 1e6)    # Mbit/s

    label = os.path.basename(name).replace(".csv", "")
    average = (nbytes[-1] - nbytes[0]) * 8 / (times[-1] - times[0]) / 1e6
    print("%s: average throughput %.2f Mbit/s" % (label, average))
    plt.plot(t, thr, styles[i % 4], color="black", linewidth=1, label=label)

if args.link > 0:
    plt.axhline(args.link, color="0.6", linewidth=1)
    plt.text(0.01, args.link, "link %g Mbit/s" % args.link, va="bottom", color="0.4",
             transform=plt.gca().get_yaxis_transform())    # x in axes units, y in Mbit/s

plt.xlabel("time (s)")
plt.ylabel("throughput (Mbit/s)")
plt.ylim(bottom=0)
plt.grid(color="0.85")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig(args.out, dpi=150)
print("plot saved in", args.out)
