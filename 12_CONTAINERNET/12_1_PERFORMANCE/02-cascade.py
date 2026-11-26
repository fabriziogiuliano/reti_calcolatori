from mininet.net import Containernet
from mininet.node import OVSBridge
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

setLogLevel('info')

net = Containernet(controller=None)

h1 = net.addHost('h1', ip='10.0.0.1')
h2 = net.addHost('h2', ip='10.0.0.2')

s1 = net.addSwitch('s1', cls=OVSBridge)
s2 = net.addSwitch('s2', cls=OVSBridge)
s3 = net.addSwitch('s3', cls=OVSBridge)
s4 = net.addSwitch('s4', cls=OVSBridge)
s5 = net.addSwitch('s5', cls=OVSBridge)

net.addLink(h1, s1)
net.addLink(s1, s2, cls=TCLink, bw=10, delay='10ms')
net.addLink(s2, s3, cls=TCLink, bw=10, delay='10ms')
net.addLink(s3, s4, cls=TCLink, bw=10, delay='10ms')
net.addLink(s4, s5, cls=TCLink, bw=10, delay='10ms')
net.addLink(s5, h2)

net.start()
CLI(net)
net.stop()
