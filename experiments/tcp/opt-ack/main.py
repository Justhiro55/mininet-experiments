#!/usr/bin/python

from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

import time
import sys
import threading
import os

# Import custom modules
from topology import DumbbellTopo
from network_setup import setup_routing
from traffic_monitor import monitor_traffic, periodic_throughput_measurement
from traffic_generator import start_normal_traffic, start_optimistic_acking_attack
from report_generator import generate_throughput_report

def main():
    setLogLevel('info')

    # Create data directory
    data_dir = './data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")

    # Setup and start network
    topo = DumbbellTopo()
    net = Mininet(topo=topo, link=TCLink)
    net.start()
    setup_routing(net)

    # Verify connections
    print("Verifying network connections:")
    dumpNodeConnections(net.hosts)

    # Start monitoring
    monitor_traffic(net)
    start_normal_traffic(net)

    # Start throughput measurements in separate thread
    print("Starting throughput monitoring...")
    monitor_thread = threading.Thread(target=periodic_throughput_measurement, args=(net, 1.0, 15))
    monitor_thread.daemon = True

    try:
        monitor_thread.start()

        # Launch attack after delay
        print("Waiting 5 seconds before starting attack...")
        time.sleep(5)
        start_optimistic_acking_attack(net)

        # Wait for monitoring to complete
        print("Monitoring throughput for 15 seconds...")
        monitor_thread.join(timeout=20)  # Extended timeout
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user.")
    except Exception as e:
        print(f"\nError during monitoring: {e}")

    # Allow thread completion
    time.sleep(2)

    # Generate final report
    try:
        generate_throughput_report()
    except Exception as e:
        print(f"Error generating throughput report: {e}")

    # Start command line interface
    CLI(net)

    # Cleanup
    net.stop()

if __name__ == '__main__':
    main()
