from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI

# Creazione dell'oggetto rete
# controller=None: no controller, so nobody fills the table of s1
net = Mininet(controller=None)
# Creazione dei nodi Host
#h1 = net.addHost( 'h1' )
#h2 = net.addHost( 'h2' )

h1 = net.addHost('h1', mac='00:00:00:00:00:01')
h2 = net.addHost('h2', mac='00:00:00:00:00:02')

# Creazione dello switch
s1 = net.addSwitch( 's1' )

# Creazione dei link
net.addLink( h1, s1 )
net.addLink( h2, s1 )
# Attivazione della rete emulata
net.start()
# Escuzione del comando ping (fallisce)
print(h1.cmd( 'ping -c1', h2.IP() ))
# Apertura della Command Line Interface (CTRL + d per usire)
CLI( net )
# Distruzione della rete emulata
net.stop()
