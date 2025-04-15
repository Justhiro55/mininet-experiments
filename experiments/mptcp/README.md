## MPTCP Test

### MPTCP Throughput Test(`mptcp-throughput-test.py`)
This simulation compares throughput between single-path TCP and Multipath TCP (MPTCP) using Mininet.

#### Topology

The following dual-path topology is used for testing:

`
h1 ── s1 ── s2 ── h2
`
- Two 5 Mbps links between `h1` and `h2`
- MPTCP enabled with two subflows

####  Test Overview
- Configures MPTCP endpoints
- Runs throughput tests for:
  - **Single Path** (1 subflow)
  - **MPTCP** (2 subflows)

#### Example Result
 ```
   Single Path (5Mbps): 4.79 Mbits/sec
   MPTCP (2 x 5Mbps): 9.15 Mbits/sec
   Throughput Improvement: 91.02%
 ```
