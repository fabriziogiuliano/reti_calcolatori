#!/usr/bin/env python
"""
A line of three OpenFlow switches, for the controller template_read.py.

    h1 --- s1 ---[10 Mbit/s, 5 ms]--- s2 ---[20 Mbit/s, 10 ms]--- s3 --- h2
    10.0.0.1                                                          10.0.0.2

Start the controller first (python run_controller.py template_read), then, from
this folder, with the conda environment cn active:
    sudo "$CONDA_PREFIX/bin/python" topology.py
"""
# mininet.net must be imported first: in Containernet, importing
# mininet.link before it fails with a circular import error
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import OVSKernelSwitch, RemoteController


def main():
    setLogLevel('info')
    net = Mininet(controller=None, switch=OVSKernelSwitch, link=TCLink,
                  autoSetMacs=True, waitConnected=True)
    net.addController('c0', controller=RemoteController,
                      ip='127.0.0.1', port=6653)

    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    s1, s2, s3 = [net.addSwitch(s, protocols='OpenFlow13')
                  for s in ('s1', 's2', 's3')]

    # port 1 of each switch towards h1, port 2 towards h2
    net.addLink(h1, s1)
    net.addLink(s1, s2, bw=10, delay='5ms')
    net.addLink(s2, s3, bw=20, delay='10ms')
    net.addLink(s3, h2)

    net.build()
    # no IPv6: otherwise the Linux kernel sends IPv6 Router Solicitations
    # from every interface, and the counters are never still
    for node in (h1, h2, s1, s2, s3):
        for intf in node.intfNames():
            if intf != 'lo':
                node.cmd('sysctl -qw net.ipv6.conf.%s.disable_ipv6=1' % intf)

    net.start()
    # forwarding without the controller: every switch behaves as a normal
    # switch (priority 0, so the rules of the controller come first)
    for s in (s1, s2, s3):
        s.cmd('ovs-ofctl -O OpenFlow13 add-flow', s.name, 'priority=0,actions=normal')
    CLI(net)
    net.stop()


if __name__ == '__main__':
    main()
