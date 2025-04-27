# Optimistic ACKing Attack Simulation

This project simulates an Optimistic ACKing attack in a dumbbell topology network using Mininet.

## File Structure

- `main.py` - Main execution script
- `topology.py` - Network topology definition
- `network_setup.py` - IP address and routing configuration
- `traffic_monitor.py` - Network traffic monitoring functions
- `traffic_generator.py` - Normal and attack traffic generation
- `report_generator.py` - Traffic analysis and report generation
- `optack.py` - Optimistic ACKing attack implementation script

## Requirements

- Mininet
- Python 3
- matplotlib
- pandas
- numpy

## Usage

1. Make sure all Python files have execution permissions:
   ```
   chmod +x *.py
   ```

2. Run the simulation as root:
   ```
   sudo python3 main.py
   ```

3. The simulation will:
   - Set up a dumbbell network topology with 2 routers and 4 hosts
   - Start regular TCP traffic
   - After 5 seconds, initiate an Optimistic ACKing attack
   - Monitor and record throughput for 15 seconds
   - Generate a throughput graph and report
   - Launch the Mininet CLI for further interaction

4. Examine the results:
   - The throughput graph is saved at `./data/throughput_graph.png`
   - The attack report is saved at `./data/attack_report.txt`
   - Network traffic capture is saved at `./data/bottleneck.pcap`
   - Various log files are created in `./data/`

## Network Topology

```
      tc                     ts
       |                     |
       |                     |
       |                     |
      r1 -----------------  r2
       |                     |
       |                     |
      ac                    ats
```

where:
- tc: Target client
- ts: Target server
- ac: Attacker client
- ats: Attacker server
- r1, r2: Routers connecting the clients and servers

The link between r1 and r2 is limited to 10Mbps, while all other links are 100Mbps.
