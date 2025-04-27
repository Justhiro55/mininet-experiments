#!/bin/bash

SCRIPT_DIR="$(pwd)"
DURATION=30
BOTTLENECK_BW=10

cleanup() {
    echo "Cleaning up environment..."
    sudo killall -9 python3 tcpdump iperf iperf3 2>/dev/null
    
    for ns in $(sudo ip netns list | cut -d' ' -f1); do
        [ -n "$ns" ] && sudo ip netns delete $ns 2>/dev/null
    done
    
    rm -f ./combined_traffic.pcap 2>/dev/null
    
    echo "Cleanup complete"
}

setup_dumbbell_network() {
    echo "Building dumbbell network topology..."
    
    for ns in client1 client2 router1 router2 server1 server2; do
        sudo ip netns add $ns
    done
    
    # Create veth pairs
    sudo ip link add c1-r1 type veth peer name r1-c1
    sudo ip link add c2-r1 type veth peer name r1-c2
    
    # Bottleneck link
    sudo ip link add r1-r2 type veth peer name r2-r1
    
    sudo ip link add r2-s1 type veth peer name s1-r2
    sudo ip link add r2-s2 type veth peer name s2-r2
    
    # Assign interfaces
    sudo ip link set c1-r1 netns client1
    sudo ip link set c2-r1 netns client2
    
    sudo ip link set r1-c1 netns router1
    sudo ip link set r1-c2 netns router1
    sudo ip link set r1-r2 netns router1
    
    sudo ip link set r2-r1 netns router2
    sudo ip link set r2-s1 netns router2
    sudo ip link set r2-s2 netns router2
    
    sudo ip link set s1-r2 netns server1
    sudo ip link set s2-r2 netns server2
    
    # Enable interfaces
    sudo ip netns exec client1 ip link set lo up
    sudo ip netns exec client1 ip link set c1-r1 up
    sudo ip netns exec client2 ip link set lo up
    sudo ip netns exec client2 ip link set c2-r1 up
    
    sudo ip netns exec router1 ip link set lo up
    sudo ip netns exec router1 ip link set r1-c1 up
    sudo ip netns exec router1 ip link set r1-c2 up
    sudo ip netns exec router1 ip link set r1-r2 up
    
    sudo ip netns exec router2 ip link set lo up
    sudo ip netns exec router2 ip link set r2-r1 up
    sudo ip netns exec router2 ip link set r2-s1 up
    sudo ip netns exec router2 ip link set r2-s2 up
    
    sudo ip netns exec server1 ip link set lo up
    sudo ip netns exec server1 ip link set s1-r2 up
    sudo ip netns exec server2 ip link set lo up
    sudo ip netns exec server2 ip link set s2-r2 up
    
    # IP addresses
    sudo ip netns exec client1 ip addr add 10.0.1.1/24 dev c1-r1
    sudo ip netns exec client2 ip addr add 10.0.2.1/24 dev c2-r1
    
    sudo ip netns exec router1 ip addr add 10.0.1.254/24 dev r1-c1
    sudo ip netns exec router1 ip addr add 10.0.2.254/24 dev r1-c2
    sudo ip netns exec router1 ip addr add 10.0.3.1/24 dev r1-r2
    
    sudo ip netns exec router2 ip addr add 10.0.3.2/24 dev r2-r1
    sudo ip netns exec router2 ip addr add 10.0.4.254/24 dev r2-s1
    sudo ip netns exec router2 ip addr add 10.0.5.254/24 dev r2-s2
    
    sudo ip netns exec server1 ip addr add 10.0.4.1/24 dev s1-r2
    sudo ip netns exec server2 ip addr add 10.0.5.1/24 dev s2-r2
    
    # IP forwarding
    sudo ip netns exec router1 sysctl -w net.ipv4.ip_forward=1
    sudo ip netns exec router2 sysctl -w net.ipv4.ip_forward=1
    
    # Routing
    sudo ip netns exec client1 ip route add default via 10.0.1.254
    sudo ip netns exec client2 ip route add default via 10.0.2.254
    
    sudo ip netns exec router1 ip route add 10.0.4.0/24 via 10.0.3.2
    sudo ip netns exec router1 ip route add 10.0.5.0/24 via 10.0.3.2
    
    sudo ip netns exec router2 ip route add 10.0.1.0/24 via 10.0.3.1
    sudo ip netns exec router2 ip route add 10.0.2.0/24 via 10.0.3.1
    
    sudo ip netns exec server1 ip route add default via 10.0.4.254
    sudo ip netns exec server2 ip route add default via 10.0.5.254

    # Edge links (100Mbps)
    sudo ip netns exec client1 tc qdisc add dev c1-r1 root handle 1: netem delay 5ms
    sudo ip netns exec client1 tc qdisc add dev c1-r1 root tbf rate 100mbit burst 15k latency 1ms

    sudo ip netns exec client2 tc qdisc add dev c2-r1 root handle 1: netem delay 5ms
    sudo ip netns exec client2 tc qdisc add dev c2-r1 root tbf rate 100mbit burst 15k latency 1ms

    # Bottleneck link
    sudo ip netns exec router1 tc qdisc add dev r1-r2 root handle 1: netem delay 10ms
    sudo ip netns exec router1 tc qdisc add dev r1-r2 root tbf rate ${BOTTLENECK_BW}mbit burst 15k latency 20ms

    sudo ip netns exec router2 tc qdisc add dev r2-r1 root handle 1: netem delay 10ms
    sudo ip netns exec router2 tc qdisc add dev r2-r1 root tbf rate ${BOTTLENECK_BW}mbit burst 15k latency 20ms
    
    sudo ip netns exec server1 tc qdisc add dev s1-r2 root handle 1: netem delay 5ms
    sudo ip netns exec server1 tc qdisc add dev s1-r2 root tbf rate 100mbit burst 15k latency 1ms
    
    sudo ip netns exec server2 tc qdisc add dev s2-r2 root handle 1: netem delay 5ms
    sudo ip netns exec server2 tc qdisc add dev s2-r2 root tbf rate 100mbit burst 15k latency 1ms
    
    # Connectivity check
    echo "Verifying connectivity..."
    echo -n "client1 → server1: "
    sudo ip netns exec client1 ping -c 2 -q 10.0.4.1 > /dev/null
    if [ $? -eq 0 ]; then echo "success"; else echo "failed"; fi
    
    echo -n "client2 → server2: "
    sudo ip netns exec client2 ping -c 2 -q 10.0.5.1 > /dev/null
    if [ $? -eq 0 ]; then echo "success"; else echo "failed"; fi
    
    if [ $? -ne 0 ]; then
        echo "Connectivity check failed. Performing detailed diagnosis:"
        for node in client1 client2 router1 router2 server1 server2; do
            echo "Routing table for ${node}:"
            sudo ip netns exec ${node} ip route
        done
        
        echo "Testing router1 → router2 connectivity:"
        sudo ip netns exec router1 ping -c 1 10.0.3.2
    fi
}

run_experiment() {
    local duration=$1
    
    echo -e "\n=========================================="
    echo "Experiment: Target traffic + Normal traffic (${duration} seconds)"
    echo "Configuration: Bottleneck bandwidth = ${BOTTLENECK_BW}Mbps"
    echo "=========================================="
    
    # Packet capture
    echo "Starting packet capture..."
    sudo ip netns exec router1 tcpdump -i r1-r2 -s 65535 -w "./combined_traffic.pcap" &
    TCPDUMP_PID=$!
    
    # Start servers
    echo "Starting servers..."
    sudo ip netns exec server1 iperf3 -s -p 5001 &
    SERVER1_PID=$!

    sudo ip netns exec server2 iperf3 -s -p 5001 &
    SERVER2_PID=$!

    sleep 2

    # Target traffic (t=0s)
    echo "Starting target client (0 seconds)..."
    sudo ip netns exec client1 iperf3 -c 10.0.4.1 -p 5001 -t $duration -b ${BOTTLENECK_BW}M -R &
    CLIENT1_PID=$!

    (
        sleep 3
        echo "Current bottleneck link bandwidth usage:"
        sudo ip netns exec router1 tc -s qdisc show dev r1-r2
    ) &
    
    # Competing traffic (t=5s)
    echo "Starting normal client in 5 seconds..."
    
    (
        sleep 5
        echo "Starting normal client (5 seconds)..."
        sudo ip netns exec client2 iperf3 -c 10.0.5.1 -p 5001 -t $((duration-5)) -b ${BOTTLENECK_BW}M -R
    ) &
    CLIENT2_PID=$!
    
    (
        sleep 8
        echo "Bottleneck link bandwidth usage after normal client started:"
        sudo ip netns exec router1 tc -s qdisc show dev r1-r2
    ) &

    echo "Running experiment... please wait ${duration} seconds..."
    sleep $((duration + 5))

    # Cleanup
    echo "Terminating processes..."
    sudo kill -9 $TCPDUMP_PID $SERVER1_PID $SERVER2_PID $CLIENT1_PID $CLIENT2_PID 2>/dev/null

    sleep 2

    echo "Experiment completed"
}

main() {
    DURATION=30
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --duration)
                DURATION="$2"
                shift 2
                ;;
            --bottleneck)
                BOTTLENECK_BW="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--duration seconds] [--bottleneck bandwidth(Mbps)]"
                exit 1
                ;;
        esac
    done

    cleanup
    setup_dumbbell_network
    
    if ping_success=$(sudo ip netns exec client2 ping -c 1 -q 10.0.5.1 2>/dev/null); then
        run_experiment $DURATION
        
        echo -e "\nExperiment completed. Capture file is available at:"
        echo "- ./combined_traffic.pcap (contains both traffic types)"

        echo -e "\nExample Wireshark data analysis command:"
        echo "wireshark ./combined_traffic.pcap"

        echo -e "\nExample Wireshark bandwidth analysis filters:"
        echo "ip.addr==10.0.4.1  # server1 (target) traffic"
        echo "ip.addr==10.0.5.1  # server2 (normal) traffic"
    else
        echo "Network configuration issue detected. Experiment aborted."
    fi
}

main "$@"
