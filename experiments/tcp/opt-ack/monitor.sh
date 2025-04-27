#!/bin/bash
echo "Time(s),Interface,RX_Mbps,TX_Mbps" > ./data/router_throughput.csv
INTERVAL=1
COUNT=60

prev_rx=0
prev_tx=0

for i in $(seq 1 $COUNT); do
    # Get network statistics for r1-eth2
    line=$(cat /proc/net/dev | grep r1-eth2)

    # Get RX and TX bytes
    rx_bytes=$(echo $line | awk '{print $2}')
    tx_bytes=$(echo $line | awk '{print $10}')

    if [ $i -gt 1 ]; then
        # Calculate difference from previous measurement
        rx_bps=$(( (rx_bytes - prev_rx) * 8 / INTERVAL ))
        tx_bps=$(( (tx_bytes - prev_tx) * 8 / INTERVAL ))

        # Convert to Mbps
        rx_mbps=$(echo "scale=2; $rx_bps/1000000" | bc)
        tx_mbps=$(echo "scale=2; $tx_bps/1000000" | bc)

        # Record results
        echo "$i,r1-eth2,$rx_mbps,$tx_mbps" >> ./data/router_throughput.csv

        # Display state before/after attack
        phase="BEFORE ATTACK"
        if [ $i -gt 5 ]; then
            phase="DURING ATTACK"
        fi
        echo "[$i s] $phase: RX: $rx_mbps Mbps, TX: $tx_mbps Mbps"
    fi

    # Save current values
    prev_rx=$rx_bytes
    prev_tx=$tx_bytes

    sleep $INTERVAL
done
