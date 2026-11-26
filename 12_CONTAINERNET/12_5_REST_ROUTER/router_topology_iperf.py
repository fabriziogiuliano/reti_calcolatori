from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo
from mininet.link import TCLink
import time

#guide here: https://osrg.github.io/ryu-book/en/html/rest_router.html



def run_iperf(net):
    # Recuperiamo i due host
    h1, h2 = net.get('h1', 'h2')
                
    # Avviamo iperf su h1 in modalità server
    print("Avvio iperf su h1 in modalità server...")
    #h1.cmd('iperf -s -i1> iperf_server_output.txt &')
    h1.cmd('iperf -s -i1 -u -p5002 > iperf_server_output.txt &')
    print("delay 2 sec...")
    time.sleep(2)

    #CLI(net)

    # Avviamo iperf su h2 in modalità client verso h1
    print("Avvio iperf su h2 in modalità client verso h1...")
    result = h2.cmd('iperf -c {} -u -p5002 -t 10 -b1M -i1 > iperf_client_output.txt'.format(h1.IP()))
    # Mostriamo il risultato di iperf
    print("Risultato iperf LATO CLIENT:")
    print(result)


class MyTopology(Topo):
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)


        # Add hosts
        h1 = self.addHost('h1', ip='10.1.1.1/24')
        h2 = self.addHost('h2', ip='192.168.1.2/24')


        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Add links
        self.addLink(h1, s1,cls=TCLink, bw=1,delay="2ms",use_htb=False)
        self.addLink(s1, s2,cls=TCLink,bw=1,delay="5ms",use_htb=False)
        self.addLink(s2, h2,cls=TCLink,bw=1,delay="2ms",use_htb=False)

def topology():
    net = Mininet(controller=RemoteController, switch=OVSKernelSwitch, autoSetMacs=True, topo=MyTopology(),link = TCLink)

    # Add controller
    #c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    c0 = RemoteController('c0', ip='127.0.0.1', port=6653, protocols="OpenFlow13")

    c0.start()
    info('*** Starting network\n')
    net.start()
    net.get("h1").cmd("ip route add default via 10.1.1.254")
    net.get("h2").cmd("ip route add default via 192.168.1.254")

    net.get("s1").cmd("ovs-vsctl set Bridge s1 protocols=OpenFlow13")
    net.get("s2").cmd("ovs-vsctl set Bridge s2 protocols=OpenFlow13")

    info(c0.cmd('curl -X POST -d \'{"address":"10.1.1.254/24"}\' http://localhost:8080/router/0000000000000001'))
    info(c0.cmd('curl -X POST -d \'{"address":"200.0.0.254/24"}\' http://localhost:8080/router/0000000000000001'))
    info(c0.cmd('curl -X POST -d \'{"address":"200.0.0.253/24"}\' http://localhost:8080/router/0000000000000002'))
    info(c0.cmd('curl -X POST -d \'{"address":"192.168.1.254/24"}\' http://localhost:8080/router/0000000000000002'))

    info(c0.cmd('curl -X POST -d \'{"gateway": "200.0.0.253"}\' http://localhost:8080/router/0000000000000001'))
    info(c0.cmd('curl -X POST -d \'{"gateway": "200.0.0.254"}\' http://localhost:8080/router/0000000000000002'))

    info('*** Running CLI\n')

    run_iperf(net)
    #CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()

