# TCP Congestion Control Simulation

## TCP Fairness Test (`tcp-fairness-test.py`, `tcp-fairness-test.sh`)
This simulation examines bandwidth sharing between two TCP flows through a bottleneck link using Mininet.

### Implementation Methods
- **tcp_fair_test.py**: Implemented using Mininet
- **tcp_fair_test.sh**: Implemented using Linux namespaces

### Topology
The dumbbell topology is used for testing:
```
client1 ──┐           ┌── server1
        router1 ── router2
client2 ──┘           └── server2
```
- Edge links: 100 Mbps with 5ms delay
- Bottleneck link: 10 Mbps with 10ms delay, 1ms jitter

### Test Overview
- Configures TCP parameters for all hosts
- Runs competing flows:
  - **Target flow**: client1 to server1 (starts at t=0s)
  - **Competing flow**: client2 to server2 (starts at t=5s)

### Example Result
The experiment confirms approximately equal (50:50) bandwidth sharing between TCP flows, demonstrating fair congestion control operation.
