#!/usr/bin/python

from mininet.topo import Topo
from mininet.node import Node

# Define a custom Linux router class
class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class DumbbellTopo(Topo):
    def build(self):
        # Create routers
        r1 = self.addNode('r1', cls=LinuxRouter)
        r2 = self.addNode('r2', cls=LinuxRouter)

        tc = self.addHost('tc')  # target_client
        ts = self.addHost('ts')  # target_server
        ac = self.addHost('ac')  # attacker_client
        ats = self.addHost('ats') # attacker_server

        # Add links between hosts and routers (r1-r2間：10Mbps, Other：100Mbps)
        self.addLink(tc, r1, bw=100, delay='10ms')
        self.addLink(ts, r2, bw=100, delay='10ms')
        self.addLink(ac, r1, bw=100, delay='10ms')
        self.addLink(ats, r2, bw=100, delay='10ms')
        self.addLink(r1, r2, bw=10, delay='10ms')  # Bottleneck link
