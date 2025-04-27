#!/bin/bash

# Set execution permissions
chmod +x *.py

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Check for required packages
echo "Checking for required packages..."

# Check for Mininet
if ! command -v mn &> /dev/null; then
  echo "Mininet not found. Please install Mininet."
  exit 1
fi

# Check for Python packages
python3 -c "import matplotlib, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Installing required Python packages..."
  pip3 install matplotlib pandas numpy
fi

# Check for iperf
if ! command -v iperf &> /dev/null; then
  echo "Installing iperf..."
  apt-get update
  apt-get install -y iperf
fi

echo "All dependencies are installed."
echo "You can now run the simulation with: sudo python3 main.py"
