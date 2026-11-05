#!/usr/bin/env python
# Plot the cwnd of one or more CSV files written by cwnd_client.py

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")    # no window: only write the image file
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("files", nargs="+", help="CSV files, e.g. reno.csv cubic.csv")
parser.add_argument("--out", default="cwnd.png", help="image file (.png, .svg, .pdf)")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

# read all the files
curves = []
for name in args.files:
    times = []
    cwnd = []
    for row in csv.DictReader(open(name)):
        times.append(float(row["time"]))
        cwnd.append(int(row["cwnd"]))
    curves.append([name, times, cwnd])

# time 0 = the first sample of all the files
t0 = min(curve[1][0] for curve in curves)

styles = ["-", "--", ":", "-."]    # one line style per file, black and white
plt.figure(figsize=(9, 4))
for i, curve in enumerate(curves):
    name = curve[0]
    t = [x - t0 for x in curve[1]]
    cwnd = curve[2]
    plt.plot(t, cwnd, styles[i % 4], color="black", linewidth=1, label=os.path.basename(name).replace(".csv", ""))

plt.xlabel("time (s)")
plt.ylabel("cwnd (segments)")
plt.grid(color="0.85")
plt.legend()
plt.tight_layout()
plt.savefig(args.out, dpi=150)
print("plot saved in", args.out)
