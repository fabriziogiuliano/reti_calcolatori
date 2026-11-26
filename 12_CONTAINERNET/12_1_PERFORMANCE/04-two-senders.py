from mininet.net import Containernet
from mininet.node import OVSBridge
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

setLogLevel('info')

net = Containernet(controller=None)

h1 = net.addHost('h1', ip='10.0.0.1')
h2 = net.addHost('h2', ip='10.0.0.2')
h3 = net.addHost('h3', ip='10.0.0.3')

s1 = net.addSwitch('s1', cls=OVSBridge)
s2 = net.addSwitch('s2', cls=OVSBridge)

net.addLink(h1, s1)
net.addLink(h3, s1)
net.addLink(s1, s2, cls=TCLink, bw=10)   # shared by h1 and h3
net.addLink(s2, h2)

net.start()
CLI(net)
net.stop()
