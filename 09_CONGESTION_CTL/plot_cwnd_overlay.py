#!/usr/bin/env python
# Overlay the cwnd of experiments run at different moments (e.g. reno.csv, then cubic.csv)
# Each file starts at its own time 0. For clients that ran together, use plot_cwnd.py.

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")    # no window: only write the image file
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("files", nargs="+", help="CSV files, e.g. reno.csv cubic.csv")
parser.add_argument("--out", default="cwnd_overlay.png", help="image file (.png, .svg, .pdf)")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

styles = ["-", "--", ":", "-."]    # one line style per file, black and white
plt.figure(figsize=(9, 4))
for i, name in enumerate(args.files):
    times = []
    cwnd = []
    for row in csv.DictReader(open(name)):
        times.append(float(row["time"]))
        cwnd.append(int(row["cwnd"]))

    # time 0 = the first sample of THIS file: the experiments line up at their start
    t = [x - times[0] for x in times]

    label = os.path.basename(name).replace(".csv", "")
    print("%s: %.1f s, average cwnd %.0f segments" % (label, t[-1], sum(cwnd) / len(cwnd)))
    plt.plot(t, cwnd, styles[i % 4], color="black", linewidth=1, label=label)

plt.xlabel("time since the start of each experiment (s)")
plt.ylabel("cwnd (segments)")
plt.grid(color="0.85")
plt.legend()
plt.tight_layout()
plt.savefig(args.out, dpi=150)
print("plot saved in", args.out)
