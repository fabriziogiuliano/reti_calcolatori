#!/bin/bash
# Bottleneck emulator on the loopback (Linux / WSL only), for the traffic to/from port 12000
#
#   ./emulate_channel.sh start     start (or restart) the emulator with the values below
#   ./emulate_channel.sh stop      remove the emulator
#   ./emulate_channel.sh show      show the current settings
#
# Change the values here, or set them on the command line:
#   DELAY=200ms LOSS=0.1% QUEUE=100 ./emulate_channel.sh start

DELAY=${DELAY:-100ms}    # one-way delay of the cable (on the ACK path): RTT ≈ DELAY
LOSS=${LOSS:-0%}         # random loss of the data packets, e.g. 0.1%
QUEUE=${QUEUE:-50}       # router queue, in packets (same on both directions)
RATE=${RATE:-10mbit}     # link speed (same on both directions)
PORT=12000

case "$1" in
start)
    sudo tc qdisc del dev lo root 2>/dev/null    # remove old settings, if any
    sudo ethtool -K lo tso off gso off           # real segments, not 64 KB blocks
    sudo tc qdisc add dev lo root handle 1: prio
    # data: router queue + link (+ random loss)
    sudo tc qdisc add dev lo parent 1:1 handle 10: netem rate $RATE limit $QUEUE loss $LOSS
    # ACKs: cable (room for 1500 packets), then router queue + link (queue in bytes: 1040 per packet)
    sudo tc qdisc add dev lo parent 1:3 handle 30: netem delay $DELAY limit 1500
    sudo tc qdisc add dev lo parent 30:1 handle 31: tbf rate $RATE burst 1540 limit $((QUEUE * 1040))
    # which packets go where: to port 12000 = data, from port 12000 = ACKs
    sudo tc filter add dev lo parent 1: protocol ip u32 match ip dport $PORT 0xffff flowid 1:1
    sudo tc filter add dev lo parent 1: protocol ip u32 match ip sport $PORT 0xffff flowid 1:3
    echo "emulator on: delay $DELAY, loss $LOSS, queue $QUEUE packets, rate $RATE"
    ;;
stop)
    sudo tc qdisc del dev lo root 2>/dev/null
    sudo ethtool -K lo tso on gso on
    echo "emulator off"
    ;;
show)
    tc qdisc show dev lo
    ;;
*)
    echo "usage: [DELAY=100ms] [LOSS=0%] [QUEUE=50] [RATE=10mbit] $0 start | stop | show"
    exit 1
    ;;
esac
