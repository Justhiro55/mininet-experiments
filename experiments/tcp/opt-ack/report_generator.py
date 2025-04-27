#!/usr/bin/python

import os

def generate_throughput_report():
    """Generate a report on throughput during the optimistic ACKing attack."""

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    try:
        # Check if data directory exists
        if not os.path.exists('./data'):
            os.makedirs('./data')
            print("Created data directory: ./data")

        # Check if throughput_log.csv exists
        if not os.path.exists('./data/throughput_log.csv'):
            print("Error: throughput_log.csv not found. Please run the experiment first.")
            return

        df = pd.read_csv('./data/throughput_log.csv')

        # Plot the throughput data
        plt.figure(figsize=(10, 6))
        plt.plot(df['Time'], df['Target_Throughput_Mbps'], label='Target Traffic')
        plt.plot(df['Time'], df['Attacker_Throughput_Mbps'], label='Attacker Traffic')
        plt.plot(df['Time'], df['Total_Throughput_Mbps'], label='Total Traffic', linestyle='--')

        # Highlight the attack period
        plt.axvline(x=5, color='r', linestyle='--', label='Attack Starts')

        plt.title('Optimistic ACKing Attack: Throughput Impact')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Throughput (Mbps)')
        plt.legend()
        plt.grid(True)

        # Add a horizontal line for the bottleneck capacity
        plt.axhline(y=10, color='k', linestyle=':', label='Bottleneck Capacity (10 Mbps)')

        # Save the plot
        plt.savefig('./data/throughput_graph.png')
        print("Throughput graph saved to ./data/throughput_graph.png")

        # Calculate statistics
        pre_attack = df[df['Time'] < 5]
        post_attack = df[df['Time'] >= 5]

        # Check if there is enough data
        if len(pre_attack) == 0 or len(post_attack) == 0:
            print("Error: Not enough data for analysis. Ensure experiment captures pre and post attack phases.")
            return

        pre_target_avg = pre_attack['Target_Throughput_Mbps'].mean()
        post_target_avg = post_attack['Target_Throughput_Mbps'].mean()
        pre_attacker_avg = pre_attack['Attacker_Throughput_Mbps'].mean()
        post_attacker_avg = post_attack['Attacker_Throughput_Mbps'].mean()

        # Generate report
        with open('./data/attack_report.txt', 'w') as f:
            f.write("Optimistic ACKing Attack Report\n")
            f.write("==============================\n\n")
            f.write(f"Target Traffic (Before Attack): {pre_target_avg:.2f} Mbps\n")
            f.write(f"Target Traffic (During Attack): {post_target_avg:.2f} Mbps\n")

            reduction = (1 - post_target_avg/pre_target_avg)*100
            f.write(f"Throughput Reduction: {reduction:.2f}%\n\n")

            f.write(f"Attacker Traffic (Before Attack): {pre_attacker_avg:.2f} Mbps\n")
            f.write(f"Attacker Traffic (During Attack): {post_attacker_avg:.2f} Mbps\n\n")
            f.write("Total Traffic:\n")
            f.write(f"  Before Attack: {pre_attack['Total_Throughput_Mbps'].mean():.2f} Mbps\n")
            f.write(f"  During Attack: {post_attack['Total_Throughput_Mbps'].mean():.2f} Mbps\n")

        print("Attack report saved to ./data/attack_report.txt")
    except Exception as e:
        import traceback
        print(f"Error generating report: {e}")
        print(traceback.format_exc())
