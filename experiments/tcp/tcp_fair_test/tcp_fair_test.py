#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Host
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

import time
import os
import subprocess
from subprocess import Popen, PIPE
import shlex

class DumbbellTopo(Topo):
    """Dumbbell topology with two clients, two routers, and two servers."""
    
    def build(self, bw_bottleneck=10):
        client1 = self.addHost('client1')
        client2 = self.addHost('client2')
        server1 = self.addHost('server1')
        server2 = self.addHost('server2')
        router1 = self.addSwitch('r1')
        router2 = self.addSwitch('r2')
        
        # Edge links: 100Mbps
        self.addLink(client1, router1, bw=100, delay='5ms')
        self.addLink(client2, router1, bw=100, delay='5ms')
        
        # Bottleneck link
        self.addLink(router1, router2, bw=bw_bottleneck, delay='10ms',
                    jitter='1ms', max_queue_size=17, use_tbf=True)
        
        self.addLink(router2, server1, bw=100, delay='5ms')
        self.addLink(router2, server2, bw=100, delay='5ms')

def start_tcpdump(net, output_file="./combined_traffic.pcap"):
    print("Starting packet capture...")
    r1 = net.get('r1')
    iface = r1.connectionsTo(net.get('r2'))[0][0].name
    
    cmd = f"tcpdump -i {iface} -s 65535 -w {output_file}"
    process = r1.popen(shlex.split(cmd))
    return process

def check_connections(net):
    print("Testing network connectivity...")
    
    client1, server1 = net.get('client1', 'server1')
    result = client1.cmd(f'ping -c 2 -q {server1.IP()}')
    print(f"client1 → server1: {'Success' if ' 0% packet loss' in result else 'Failed'}")
    
    client2, server2 = net.get('client2', 'server2')
    result = client2.cmd(f'ping -c 2 -q {server2.IP()}')
    print(f"client2 → server2: {'Success' if ' 0% packet loss' in result else 'Failed'}")

def setup_tcp_congestion(net, algorithm='cubic'):
    print(f"Setting TCP congestion control algorithm to {algorithm}...")
    for host in net.hosts:
        host.cmd(f'sysctl -w net.ipv4.tcp_congestion_control={algorithm}')

def configure_tcp_params(net):
    print("Configuring TCP parameters for better fairness...")
    for host in net.hosts:
        # TCP optimization
        host.cmd('sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"')
        host.cmd('sysctl -w net.ipv4.tcp_wmem="4096 16384 16777216"')
        host.cmd('sysctl -w net.ipv4.tcp_no_metrics_save=1')
        host.cmd('sysctl -w net.ipv4.tcp_slow_start_after_idle=0')
        host.cmd('sysctl -w net.ipv4.tcp_initial_cwnd=10')
        host.cmd('sysctl -w net.ipv4.tcp_ecn=1')
        host.cmd('sysctl -w net.ipv4.tcp_adv_win_scale=1')
        host.cmd('sysctl -w net.ipv4.tcp_app_win=31')
        host.cmd('sysctl -w net.ipv4.tcp_moderate_rcvbuf=1')

def display_tc_config(net):
    r1, r2 = net.get('r1', 'r2')
    
    print("\nRouter1 interface TC configuration:")
    iface = r1.connectionsTo(r2)[0][0].name
    print(r1.cmd(f'tc -d qdisc show dev {iface}'))
    
    print("\nRouter2 interface TC configuration:")
    iface = r2.connectionsTo(r1)[0][0].name
    print(r2.cmd(f'tc -d qdisc show dev {iface}'))

def run_experiment(net, duration=30):
    print("=" * 50)
    print(f"Experiment: Target traffic + Normal traffic ({duration} seconds)")
    bw_bottleneck = net.topo.linkInfo('r1', 'r2')['bw']
    print(f"Experiment configuration: Bottleneck bandwidth = {bw_bottleneck}Mbps")
    print("=" * 50)
    
    # Packet capture
    tcpdump_process = start_tcpdump(net)
    
    client1, client2 = net.get('client1', 'client2')
    server1, server2 = net.get('server1', 'server2')
    
    display_tc_config(net)
    
    # Start servers
    print("Starting servers...")
    server1.cmd('iperf3 -s -p 5001 &')
    server2.cmd('iperf3 -s -p 5001 &')
    time.sleep(2)
    
    configure_tcp_params(net)
    
    # Target traffic (t=0s)
    print("Starting target client (0 seconds)...")
    client1.cmd(f'iperf3 -c {server1.IP()} -p 5001 -t {duration} -b {bw_bottleneck}M -R -Z -w 256K &')
    
    # Check bandwidth
    time.sleep(3)
    r1 = net.get('r1')
    iface = r1.connectionsTo(net.get('r2'))[0][0].name
    print(r1.cmd(f'tc -s qdisc show dev {iface}'))
    
    # Competing traffic (t=5s)
    print("Starting normal client in 5 seconds...")
    time.sleep(2)
    print("Starting normal client (5 seconds)...")
    client2.cmd(f'iperf3 -c {server2.IP()} -p 5001 -t {duration-5} -b {bw_bottleneck}M -R -Z -w 256K &')
    
    # Monitor bandwidth
    time.sleep(3)
    print("Bandwidth usage after normal client starts:")
    print(r1.cmd(f'tc -s qdisc show dev {iface}'))
    
    # Periodic monitoring
    print("Monitoring bandwidth usage every 5 seconds...")
    for i in range(1, duration//5):
        time.sleep(5)
        print(f"\nBandwidth usage at {5*i+8} seconds:")
        print(r1.cmd(f'tc -s qdisc show dev {iface}'))
        
        print("\nTCP connection states:")
        for host in [client1, client2, server1, server2]:
            print(f"\n{host.name} TCP connections:")
            print(host.cmd('ss -tni'))
    
    # Complete experiment
    remaining_time = duration - (5 * (duration//5)) + 2
    if remaining_time > 0:
        time.sleep(remaining_time)
    
    # Cleanup
    print("Stopping capture and cleaning up...")
    tcpdump_process.terminate()
    os.system("sudo killall -9 iperf3 > /dev/null 2>&1")
    
    print("Experiment completed.")
    print(f"\nCapture file is available at: ./combined_traffic.pcap")
    print("\nWireshark data analysis command:")
    print("wireshark ./combined_traffic.pcap")
    print("\nWireshark filter examples:")
    print(f"ip.addr=={server1.IP()}  # server1 (target) traffic")
    print(f"ip.addr=={server2.IP()}  # server2 (normal) traffic")

def main():
    # Experiment parameters
    duration = 30
    bw_bottleneck = 10
    tcp_algorithm = 'cubic'
    
    # Parse CLI arguments
    import sys
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--duration" and i+1 < len(sys.argv):
            duration = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--bottleneck" and i+1 < len(sys.argv):
            bw_bottleneck = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--tcp" and i+1 < len(sys.argv):
            tcp_algorithm = sys.argv[i+1]
            i += 2
        else:
            print(f"Unknown option: {sys.argv[i]}")
            print(f"Usage: {sys.argv[0]} [--duration seconds] [--bottleneck bandwidth(Mbps)] [--tcp algorithm]")
            sys.exit(1)
    
    # Setup and run
    topo = DumbbellTopo(bw_bottleneck=bw_bottleneck)
    net = Mininet(topo=topo, host=Host, link=TCLink)
    net.start()
    
    dumpNodeConnections(net.hosts)
    setup_tcp_congestion(net, tcp_algorithm)
    check_connections(net)
    run_experiment(net, duration)
    
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
