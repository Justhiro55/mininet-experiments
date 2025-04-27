# Optimistic ACKing Attack Details

## Overview

Optimistic ACKing is a TCP-based attack where an attacker manipulates TCP's acknowledgment mechanism by sending acknowledgments for data that hasn't actually been received yet. This tricks the sender into believing that the network can handle more data than it actually can, causing it to increase its sending rate beyond what's sustainable.

## How the Attack Works

1. **Establishing Connection**:
   - The attacker establishes a normal TCP connection with the target server.

2. **Premature Acknowledgments**:
   - Instead of waiting to receive data before sending ACKs (as per normal TCP behavior), the attacker sends ACKs for packets that haven't been received yet.
   - The attacker preemptively acknowledges future sequence numbers, making the server believe its data has been successfully delivered.

3. **Window Size Manipulation**:
   - The attacker might also advertise a large receive window, encouraging the server to send more data.

4. **Impact**:
   - The server is tricked into sending data at a rate faster than the network can handle, potentially causing congestion.
   - This can lead to legitimate users experiencing degraded performance or denial of service.

## Implementation in This Simulation

The implementation in `optack.py` demonstrates this attack using the following techniques:

1. It establishes a legitimate connection to the target server (iperf server in our case).
2. It sends large data blocks to consume bandwidth.
3. It sends false ACKs with sequence numbers far ahead of what has actually been received.
4. It repeats this process rapidly, causing the server to send more data than the bottleneck link can handle.

## Detection and Mitigation

1. **Rate Limiting**:
   - Implementing rate-limiting mechanisms at the network edge.

2. **TCP Sequence Verification**:
   - Implementing systems that monitor for unusual patterns in TCP acknowledgments.

3. **Statistical Analysis**:
   - Network monitoring tools can detect abnormal ratios of data packets to ACK packets.

4. **Randomized Initial Sequence Numbers**:
   - Makes it harder for attackers to predict sequence numbers.

5. **TCP Authentication Option (TCP-AO)**:
   - Provides stronger protection against attacks that manipulate TCP segments.

## Impact Measurement

In this simulation, we measure the attack's impact by comparing:
- Throughput of legitimate traffic before and during the attack
- Total link utilization
- Packet drop rates at the bottleneck link

The graphs generated show how the attacker's traffic consumes an unfair share of the bottleneck bandwidth, reducing the legitimate user's throughput.
