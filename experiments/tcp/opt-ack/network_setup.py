#!/usr/bin/python

import time

def setup_routing(net):
    # Setting up routing
    r1 = net.get('r1')
    r2 = net.get('r2')

    # assigning IP addresses to routers
    r1.cmd('ifconfig r1-eth0 10.0.1.1/24')
    r1.cmd('ifconfig r1-eth1 10.0.3.1/24')
    r1.cmd('ifconfig r1-eth2 10.0.5.1/24')

    r2.cmd('ifconfig r2-eth0 10.0.2.1/24')
    r2.cmd('ifconfig r2-eth1 10.0.4.1/24')
    r2.cmd('ifconfig r2-eth2 10.0.5.2/24')

    # assigning IP addresses to hosts
    tc = net.get('tc')
    ts = net.get('ts')
    ac = net.get('ac')
    ats = net.get('ats')

    tc.cmd('ifconfig tc-eth0 10.0.1.2/24')
    ts.cmd('ifconfig ts-eth0 10.0.2.2/24')
    ac.cmd('ifconfig ac-eth0 10.0.3.2/24')
    ats.cmd('ifconfig ats-eth0 10.0.4.2/24')

    # Setting up default routing on hosts
    tc.cmd('route add default gw 10.0.1.1')
    ts.cmd('route add default gw 10.0.2.1')
    ac.cmd('route add default gw 10.0.3.1')
    ats.cmd('route add default gw 10.0.4.1')

    # Adding routes on routers
    r1.cmd('route add -net 10.0.2.0/24 gw 10.0.5.2')
    r1.cmd('route add -net 10.0.4.0/24 gw 10.0.5.2')

    r2.cmd('route add -net 10.0.1.0/24 gw 10.0.5.1')
    r2.cmd('route add -net 10.0.3.0/24 gw 10.0.5.1')

    # Checking connectivity
    print("Checking connectivity...")
    tc.cmd('ping -c 1 10.0.2.2')
    ts.cmd('ping -c 1 10.0.1.2')
    ac.cmd('ping -c 1 10.0.4.2')
    ats.cmd('ping -c 1 10.0.3.2')
