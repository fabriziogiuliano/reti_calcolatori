#!/usr/bin/env python
# Plot the throughput of one or more CSV files written by iperf with -y C (one line per second, with -i 1),
# as plot_thr.py of 09_CONGESTION_CTL, and print the average throughput of each flow
#   python plot_iperf.py bbr_Q250.csv cubic_Q250.csv --link 10 --from 60 --out Q250.png
#
# iperf -y C writes, for each interval: date,src_ip,src_port,dst_ip,dst_port,id,interval,bytes,bits_per_second
# (the last line is the summary of the whole run, over all the seconds: it is skipped)

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")    # no window: only write the image file
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("files", nargs="+", help="CSV files of iperf -y C, e.g. bbr_Q250.csv cubic_Q250.csv")
parser.add_argument("--out", default="thr.png", help="image file (.png, .svg, .pdf)")
parser.add_argument("--link", type=float, default=0,
                    help="link capacity in Mbit/s, drawn as a line: the RATE of emulate_channel.sh (0 = no line)")
parser.add_argument("--from", dest="start", type=float, default=0,
                    help="also print the average from this second on (the steady state, after the transient)")
if len(sys.argv) == 1:     # no parameters: show the help
    parser.print_help()
    sys.exit()
args = parser.parse_args()

styles = ["-", "--", ":", "-."]    # one line style per file, black and white
plt.figure(figsize=(9, 4))
for i, name in enumerate(args.files):
    t = []      # end of each 1-second interval (s)
    thr = []    # throughput in that second (Mbit/s)
    for row in csv.reader(open(name)):
        start, end = (float(x) for x in row[6].split("-"))    # interval, e.g. "12.0-13.0"
        if end - start > 1.5:                                  # the summary line: skip it
            continue
        t.append(end)
        thr.append(float(row[8]) / 1e6)
    label = os.path.basename(name).replace(".csv", "")
    steady = [x for s, x in zip(t, thr) if s > args.start]
    print("%s: average %.2f Mbit/s, from %g s %.2f Mbit/s" % (label, sum(thr) / len(thr), args.start,
                                                          sum(steady) / len(steady)))
    plt.plot(t, thr, styles[i % 4], color="black", linewidth=1, label=label)

if args.link > 0:
    plt.axhline(args.link, color="0.6", linewidth=1)
    plt.text(0.01, args.link, "link %g Mbit/s" % args.link, va="bottom", color="0.4",
             transform=plt.gca().get_yaxis_transform())    # x in axes units, y in Mbit/s
if args.start > 0:
    plt.axvline(args.start, color="0.6", linewidth=1, linestyle=":")
    plt.text(args.start, 0.01, " steady state from here", color="0.4",
             transform=plt.gca().get_xaxis_transform())    # x in seconds, y in axes units

plt.xlabel("time (s)")
plt.ylabel("throughput (Mbit/s)")
plt.ylim(bottom=0)
plt.grid(color="0.85")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig(args.out, dpi=150)
print("plot saved in", args.out)
