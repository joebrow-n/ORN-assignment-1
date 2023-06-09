from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time
import os


def assignmentTopo():
    net = Mininet( controller=RemoteController)
    
    info( '*** Adding controller\n' )
    net.addController('c0')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
    h3 = net.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')
    h4 = net.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:04')

    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')

    info('*** Creating links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)

    info( '*** Starting network\n')
    net.start()
    
    os.system('sudo ovs-vsctl set port s1-eth3 qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0,1=@q1 -- --id=@q0 create queue other-config:min-rate=0 other-config:max-rate=50000000 -- --id=@q1 create queue other-config:min-rate=0 other-config:max-rate=100000000')
    os.system('sudo ovs-vsctl set port s1-eth4 qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0 -- --id=@q0 create queue other-config:min-rate=0 other-config:max-rate=200000000')
    
    info( '\n\n\n\n*** Testing PIR to H1 to H3\n')
    # This line corresponds to "mininet> h3 iperf -s &"
    h3.cmd('iperf -s &')
    # This line corresponds to "mininet> h1 iperf -c 10.0.0.3" - test the connection from h1 to h3
    print(h1.cmd('iperf -c %s' % h3.IP()))

    info( '\n\n\n\n*** Testing PIR to H2 to H3\n')
    print(h2.cmd('iperf -c %s' % h3.IP()))

    info( '\n\n\n\n*** Testing PIR to H2 to H4\n')
    h4.cmd('iperf -s &')
    print(h2.cmd('iperf -c %s' % h4.IP()))

    info( '\n\n\n\n*** Testing PIR to H3 to H4\n')
    print(h3.cmd('iperf -c %s' % h4.IP()))

    info( '\n\n\n\n*** Testing PIR to H1 to H2\n')
    h2.cmd('iperf -s &')
    print(h1.cmd('iperf -c %s' % h2.IP()))
   
    CLI( net )

    os.system('sudo ovs-vsctl clear Port s1-eth3 qos')
    os.system('sudo ovs-vsctl clear Port s1-eth4 qos')
    os.system('sudo ovs-vsctl --all destroy qos')
    os.system('sudo ovs-vsctl --all destroy queue')

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    assignmentTopo()


