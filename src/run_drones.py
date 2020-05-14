""" Runs multiple drones simultaneously in separate processes.
    Use the --plot option to plot the drone positions on a graph.
"""

import sys
import subprocess
from multiprocessing import Process


NUM_RXS = 4


def main():
    tx_args = []
    if "--plot" in sys.argv:
        tx_args.append("--plot")
    tx_process = Process(target=subprocess.run,
                         args=(["python3", "tx.py"] + tx_args,))
    tx_process.start()

    for rx_id in range(1, NUM_RXS + 1):
        rx_process = Process(target=subprocess.run,
            args=(["python3", "rx.py", str(rx_id)],))
        rx_process.start()


if __name__ == '__main__':
    main()
