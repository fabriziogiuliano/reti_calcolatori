#ip addr: lists the network interfaces and the addresses assigned to the machine
#(ifconfig is deprecated/not installed by default on recent distributions;
#the net-tools package is replaced by the iproute2 package, command "ip")

ip addr > output_ipaddr.txt
