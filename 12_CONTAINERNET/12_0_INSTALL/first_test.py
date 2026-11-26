from mininet.net import Containernet
from mininet.node import OVSBridge
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import info, setLogLevel

setLogLevel('info')

# controller=None: no controller, so nobody fills the table of the switch
# (without it, net.start() adds a default controller and the ping works at once)
net = Containernet(controller=None)

info('*** Adding hosts\n')
h1 = net.addHost('h1', ip='10.0.0.1')
h2 = net.addHost('h2', ip='10.0.0.2')

info('*** Adding switch\n')
# PROBLEM: the default switch waits for a controller; without one its table
# stays empty and it drops every packet -> the ping fails
#s1 = net.addSwitch('s1')
# FIX: OVSBridge, a switch that works on its own (more in the next labs)
s1 = net.addSwitch('s1', cls=OVSBridge)

info('*** Creating links\n')
net.addLink(h1, s1)# cls=TCLink, bw=10, delay='0ms')
net.addLink(h2, s1)

info('*** Starting network\n')
net.start()
# Try: h1 ping -c3 h2
CLI(net)
net.stop()
