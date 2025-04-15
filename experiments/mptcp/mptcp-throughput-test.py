#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, Controller
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
import time
import re
import os
import sys

class MPTCPTopo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(h1, s1, cls=TCLink, bw=5)
        self.addLink(s1, h2, cls=TCLink, bw=5)

        self.addLink(h1, s2, cls=TCLink, bw=5)
        self.addLink(s2, h2, cls=TCLink, bw=5)

def setupMPTCP(net):
    h1, h2 = net.get('h1', 'h2')

    info('*** MPTCP activate\n')
    for host in [h1, h2]:
        host.cmd('sysctl -w net.mptcp.enabled=1')

    info('*** set IP address\n')
    h1.cmd('ip addr add 10.0.1.1/24 dev h1-eth1')
    h2.cmd('ip addr add 10.0.1.2/24 dev h2-eth1')

    h1.cmd('ip link set h1-eth1 up')
    h2.cmd('ip link set h2-eth1 up')

    info('*** h1 interface:\n')
    info(h1.cmd('ifconfig'))
    info('*** h2 interface:\n')
    info(h2.cmd('ifconfig'))

    info('*** MPTCP endpoint\n')
    h1.cmd('ip mptcp endpoint flush')
    h2.cmd('ip mptcp endpoint flush')

    h1.cmd('ip mptcp endpoint add 10.0.0.1 dev h1-eth0 subflow')
    h1.cmd('ip mptcp endpoint add 10.0.1.1 dev h1-eth1 subflow')

    h2.cmd('ip mptcp endpoint add 10.0.0.2 dev h2-eth0 signal')
    h2.cmd('ip mptcp endpoint add 10.0.1.2 dev h2-eth1 signal')

    info('*** h1 mptcp:\n')
    info(h1.cmd('ip mptcp endpoint show'))
    info('*** h2 mptcp:\n')
    info(h2.cmd('ip mptcp endpoint show'))

    info('*** connection test\n')
    info(h1.cmd('ping -c 2 10.0.0.2'))
    info(h1.cmd('ping -c 2 10.0.1.2'))

def testSinglePath(net):
    h1, h2 = net.get('h1', 'h2')

    info('*** Test: SinglePath（5Mbps）\n')

    h1.cmd('ip mptcp endpoint flush')
    h1.cmd('ip mptcp endpoint add 10.0.0.1 dev h1-eth0 subflow')
    h1.cmd('ip mptcp endpoint add 10.0.1.1 dev h1-eth1 subflow backup')

    h2.cmd('iperf -s -p 5001 > /dev/null &')
    time.sleep(1)

    result = h1.cmd('iperf -c 10.0.0.2 -p 5001 -t 10')
    info('*** Result: SinglePath:\n')
    info(result)


    bw_match = re.search(r'(\d+\.\d+) Mbits/sec', result)
    if bw_match:
        single_bw = float(bw_match.group(1))
    else:
        single_bw = 0
        info('*** Failed\n')

    h2.cmd('pkill -9 iperf')
    time.sleep(1)

    return single_bw

def testMultiPath(net):
    h1, h2 = net.get('h1', 'h2')

    info('*** Test: Multipath（MPTCP、2 x 5Mbps）\n')

    # Multipath activation
    h1.cmd('ip mptcp endpoint flush')
    h1.cmd('ip mptcp endpoint add 10.0.0.1 dev h1-eth0 subflow')
    h1.cmd('ip mptcp endpoint add 10.0.1.1 dev h1-eth1 subflow')

    h2.cmd('mptcpize run iperf -s -p 5002 > /dev/null &')
    time.sleep(1)

    result = h1.cmd('mptcpize run iperf -c 10.0.0.2 -p 5002 -t 10')
    info('*** Result: Multipath:\n')
    info(result)

    bw_match = re.search(r'(\d+\.\d+) Mbits/sec', result)
    if bw_match:
        multi_bw = float(bw_match.group(1))
    else:
        multi_bw = 0
        info('*** Failed\n')

    info('*** MPTCP subflow status::\n')
    info(h1.cmd('ss -iaM'))

    h2.cmd('pkill -9 iperf')

    return multi_bw

def run():
    topo = MPTCPTopo()
    net = Mininet(topo=topo, link=TCLink)

    net.start()

def run():
    topo = MPTCPTopo()
    net = Mininet(topo=topo, link=TCLink)

    net.start()

    try:
        setupMPTCP(net)

        single_bw = testSinglePath(net)
        time.sleep(2)
        multi_bw = testMultiPath(net)

        info('\n*** Test Results Summary:\n')
        info('   Single Path (5Mbps): %.2f Mbits/sec\n' % single_bw)
        info('   MPTCP (2 x 5Mbps): %.2f Mbits/sec\n' % multi_bw)
        info('   Throughput Improvement: %.2f%%\n' % (((multi_bw/single_bw)-1)*100 if single_bw > 0 else 0))

        info('\n*** Starting CLI for additional testing\n')
        info('   Check subflows: h1 ss -iaM\n')
        info('   Check endpoints: h1 ip mptcp endpoint show\n')
        CLI(net)
    finally:
        net.stop()

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("This script must be run as root.")
        print("Please run with: sudo python %s" % sys.argv[0])
        sys.exit(1)

    setLogLevel('info')

    # Run
    run()
