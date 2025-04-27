#!/usr/bin/python

import time
import threading
import os

def periodic_throughput_measurement(net, interval=1.0, duration=15):
    """Function to measure throughput periodically."""

    # Get the target and attacker server names
    ts_name = 'ts'
    ats_name = 'ats'

    # Generate data directory
    with open('./data/throughput_log.csv', 'w') as f:
        f.write("Time,Target_Throughput_Mbps,Attacker_Throughput_Mbps,Total_Throughput_Mbps\n")

    start_time = time.time()
    attack_start_time = start_time + 5  # Start attack after 5 seconds

    # Execute the throughput measurement in a loop
    for i in range(int(duration / interval)):
        current_time = time.time()
        elapsed = current_time - start_time

        # Avoid measuring throughput during the attack
        ts = net.getNodeByName(ts_name)
        ats = net.getNodeByName(ats_name)

        # Measure the target throughput
        result_target = ts.cmd('cat /proc/net/dev | grep ts-eth0')
        bytes_rx_target = int(result_target.split()[1]) if result_target else 0

        # Measure the attacker's throughput
        result_attacker = ats.cmd('cat /proc/net/dev | grep ats-eth0')
        bytes_rx_attacker = int(result_attacker.split()[1]) if result_attacker else 0

        # Wait for the interval
        time.sleep(interval)

        ts = net.getNodeByName(ts_name)
        ats = net.getNodeByName(ats_name)

        # Measure the target throughput again
        result_target = ts.cmd('cat /proc/net/dev | grep ts-eth0')
        bytes_rx_target_2 = int(result_target.split()[1]) if result_target else 0

        result_attacker = ats.cmd('cat /proc/net/dev | grep ats-eth0')
        bytes_rx_attacker_2 = int(result_attacker.split()[1]) if result_attacker else 0

        # Calculate throughput (bits per second)
        try:
            target_throughput = (bytes_rx_target_2 - bytes_rx_target) * 8 / interval / 1000000
            attacker_throughput = (bytes_rx_attacker_2 - bytes_rx_attacker) * 8 / interval / 1000000
            total_throughput = target_throughput + attacker_throughput

            # Display the phase of the attack
            phase = "BEFORE ATTACK" if elapsed < 5.0 else "DURING ATTACK"

            # Save the throughput data
            with open('./data/throughput_log.csv', 'a') as f:
                f.write(f"{elapsed:.1f},{target_throughput:.2f},{attacker_throughput:.2f},{total_throughput:.2f}\n")

            # Display the throughput data
            print(f"[{elapsed:.1f}s] {phase}: Target: {target_throughput:.2f} Mbps, Attacker: {attacker_throughput:.2f} Mbps, Total: {total_throughput:.2f} Mbps")
        except Exception as e:
            print(f"Error during throughput calculation: {e}")

        # Check if the attack has started
        if elapsed >= duration:
            break

def monitor_traffic(net):
    r1 = net.get('r1')
    # Monitor the traffic on the router
    r1.cmd('tcpdump -i r1-eth2 -w ./data/bottleneck.pcap &')
    
    # Execute the router throughput monitoring script
    r1.cmd('chmod +x ./monitor.sh')
    r1.cmd('./monitor.sh > ./data/router_monitor.log 2>&1 &')
