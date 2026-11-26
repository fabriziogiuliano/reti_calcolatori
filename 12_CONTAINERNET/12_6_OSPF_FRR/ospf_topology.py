#!/usr/bin/env python
"""
Dynamic routing with OSPF (Dijkstra) on FRRouting routers in Docker containers.

            cost 20                 cost 10
    h1 --- r1 ---------------- r2 ---------------- r3 --- h2
            \\                  |                  /
       cost 5 \\         cost 5 |                 / cost 30
                \\               |               /
                  ------------- r4 --------------

Every router runs FRRouting (zebra + ospfd), configured by configs/<router>.conf.
The hosts are containers of the same image, without routing daemons.

Run, from this folder, with the conda environment cn active:
    sudo "$CONDA_PREFIX/bin/python" ospf_topology.py
"""
import base64
import os
import time

from mininet.cli import CLI
from mininet.log import info, setLogLevel
from mininet.net import Containernet

IMAGE = 'quay.io/frrouting/frr:10.4.5'
HERE = os.path.dirname(os.path.abspath(__file__))

# Every link: (node A, interface A, address A, node B, interface B, address B)
LINKS = [
    ('h1', 'h1-eth0', '192.168.1.10/24', 'r1', 'r1-eth0', '192.168.1.1/24'),
    ('h2', 'h2-eth0', '192.168.3.10/24', 'r3', 'r3-eth0', '192.168.3.1/24'),
    ('r1', 'r1-eth1', '10.0.12.1/24', 'r2', 'r2-eth1', '10.0.12.2/24'),
    ('r1', 'r1-eth2', '10.0.14.1/24', 'r4', 'r4-eth1', '10.0.14.4/24'),
    ('r2', 'r2-eth2', '10.0.23.2/24', 'r3', 'r3-eth1', '10.0.23.3/24'),
    ('r2', 'r2-eth3', '10.0.24.2/24', 'r4', 'r4-eth2', '10.0.24.4/24'),
    ('r3', 'r3-eth2', '10.0.34.3/24', 'r4', 'r4-eth3', '10.0.34.4/24'),
]
ROUTERS = ['r1', 'r2', 'r3', 'r4']
HOSTS = {'h1': '192.168.1.1', 'h2': '192.168.3.1'}   # host -> default gateway


def start_frr(router):
    "Copy configs/<router>.conf into the container, enable ospfd, start FRR"
    with open(os.path.join(HERE, 'configs', router.name + '.conf')) as f:
        conf = base64.b64encode(f.read().encode()).decode()
    router.cmd('echo %s | base64 -d > /etc/frr/frr.conf' % conf)
    router.cmd('touch /etc/frr/vtysh.conf')   # vtysh complains without it
    router.cmd('chown frr:frr /etc/frr/frr.conf /etc/frr/vtysh.conf')
    router.cmd("sed -i 's/^ospfd=no/ospfd=yes/' /etc/frr/daemons")
    router.cmd('/usr/lib/frr/frrinit.sh start')


def wait_ospf(net, timeout=60):
    "Wait until every router has a route to both host LANs"
    info('*** Waiting for OSPF to converge ')
    start = time.time()
    while time.time() - start < timeout:
        ok = all('192.168.1.0/24' in net.get(r).cmd('ip route') and
                 '192.168.3.0/24' in net.get(r).cmd('ip route')
                 for r in ROUTERS)
        if ok:
            info('done in %.0f s\n' % (time.time() - start))
            return True
        info('.')
        time.sleep(1)
    info(' not converged after %d s\n' % timeout)
    return False


def main():
    setLogLevel('info')
    net = Containernet(controller=None)

    info('*** Adding routers and hosts (image %s)\n' % IMAGE)
    for name in ROUTERS:
        # FRR needs NET_ADMIN, NET_RAW and SYS_ADMIN to manage routes
        net.addDocker(name, dimage=IMAGE, ip=None, network_mode='none',
                      cap_add=['net_admin', 'net_raw', 'sys_admin'],
                      sysctls={'net.ipv4.ip_forward': 1})
    for name in HOSTS:
        net.addDocker(name, dimage=IMAGE, ip=None, network_mode='none')

    info('*** Adding links\n')
    for a, ifa, ipa, b, ifb, ipb in LINKS:
        net.addLink(net.get(a), net.get(b), intfName1=ifa, intfName2=ifb,
                    params1={'ip': ipa}, params2={'ip': ipb})

    net.start()

    for host, gw in HOSTS.items():
        net.get(host).cmd('ip route add default via %s' % gw)

    info('*** Starting FRRouting on the routers\n')
    for name in ROUTERS:
        start_frr(net.get(name))
    wait_ospf(net)

    CLI(net)
    net.stop()


if __name__ == '__main__':
    main()
