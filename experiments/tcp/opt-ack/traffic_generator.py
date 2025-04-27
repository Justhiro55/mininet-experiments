#!/usr/bin/python

import time

def start_normal_traffic(net):
    print("Starting normal TCP traffic at time 0.0s")
    tc = net.get('tc')
    ts = net.get('ts')

    # Launch iperf server on target_server
    ts.cmd('pkill -f iperf')  # Clean up any existing iperf processes
    ts.cmd('iperf -s > ./data/ts_server.log 2>&1 &')
    time.sleep(1)

    # Check if the server is running
    server_pid = ts.cmd('pgrep -f "iperf -s"').strip()
    if server_pid:
        print(f"iperf server started on target_server with PID {server_pid}")
    else:
        print("WARNING: iperf server may not have started properly on target_server")
        # Try to start it again
        ts.cmd('iperf -s > ./data/ts_server.log 2>&1 &')
        time.sleep(1)

    # Launch iperf client on target_client
    # iperf client will connect to the server
    tc.cmd('iperf -c 10.0.2.2 -t 15 -i 1 > ./data/target_traffic.log 2>&1 &')
    print("Target traffic started")

def start_optimistic_acking_attack(net):
    print("Starting Optimistic ACKing attack at time 5.0s")
    ac = net.get('ac')
    ats = net.get('ats')

    # Launch iperf server on attacker_server
    ats.cmd('pkill -f iperf')  # Clean up any existing iperf processes
    ats.cmd('iperf -s > ./data/ats_server.log 2>&1 &')
    time.sleep(1)  # Wait for the server to start

    # Check if the server is running
    server_pid = ats.cmd('pgrep -f "iperf -s"').strip()
    if server_pid:
        print(f"iperf server started on attacker_server with PID {server_pid}")
    else:
        print("WARNING: iperf server may not have started properly on attacker_server")
        # Try again
        ats.cmd('iperf -s > ./data/ats_server.log 2>&1 &')
        time.sleep(1)

    # Execute the Optimistic ACKing attack script
    ac.cmd('python3 ./optack.py > ./data/attack.log 2>&1 &')

    # Also run normal iperf attack (with 1 second interval logging)
    ac.cmd('iperf -c 10.0.4.2 -t 55 -i 1 -w 65535 > ./data/attacker_traffic.log 2>&1 &')
    print("Attack traffic started")
