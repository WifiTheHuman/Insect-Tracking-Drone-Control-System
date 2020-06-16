""" Runs multiple drones simultaneously in separate processes.
    Use the --plot option to plot the drone positions on a graph.
"""

import sys
import subprocess
from multiprocessing import Process
import argparse

# The number of Rx drones to run. Should match the values in tx.py and rx.py.
NUM_RXS = 4


def main():
    parser = argparse.ArgumentParser(
        description='Runs a Tx and multiple Rx drones in different processes.')
    parser.add_argument(
        '-p',
        '--plot',
        action='store_true',
        help='plots the drone and target positions on a graph during execution'
    )
    args = parser.parse_args()

    processes = []

    tx_args = ['--plot'] if args.plot else []
    processes.append(
        Process(target=subprocess.run,
                args=(["python3", "tx.py"] + tx_args, )))

    for rx_id in range(1, NUM_RXS + 1):
        processes.append(
            Process(target=subprocess.run,
                    args=(["python3", "rx.py", str(rx_id)], )))

    for process in processes:
        process.start()

    # Run forever, or until interrupted.
    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("Interrupted, terminating processes...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.join()


if __name__ == '__main__':
    main()
