#!/bin/bash

# This script cleans up processes and files from the simulation

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

echo "Cleaning up simulation..."

# Kill any remaining processes
echo "Stopping any running processes..."
killall -q python3 iperf tcpdump mn

# Clean up Mininet
echo "Cleaning up Mininet..."
mn -c

# Remove existing files
echo "Removing existing files..."
rm -f ./data/throughput_graph.png ./data/attack_report.txt
rm -f ./data/bottleneck.pcap ./data/throughput_log.csv
rm -f ./data/router_throughput.csv ./data/monitor.sh
rm -f ./data/*traffic.log ./data/*server.log ./data/attack.log
rm -f ./data/optack.py ./data/router_monitor.log

echo "Cleanup complete!"
