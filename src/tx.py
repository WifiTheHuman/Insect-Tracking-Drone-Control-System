import time
import zmq
import struct
import sys
import matplotlib.pyplot as plt

import multilateration
import swarming_logic
from gps import GPSCoord
from packets import RxUpdate, TxUpdate

TX_STARTUP_PORT = 5554
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

# This must have the value 4 to work with the swarming logic.
NUM_RXS = 4

# Tx starting position. This value must match the one in rx.py
TX_START_COORDS = GPSCoord(-43.520508, 172.583089)

# Limits for the expected lat and long, used for plotting the drone positons.
MIN_LAT = -43.520833
MAX_LAT = -43.520333
MIN_LONG = 172.582833
MAX_LONG = 172.583167

# The drone ID of the transmitter drone.
TX_ID = 0

# How often the Tx should perform multilateration and send an update.
UPDATE_PERIOD_S = 1

# Timeout period for receiving updates from Rxs.
TIMEOUT_S = 3


class TimeoutException(Exception):
    pass


def wait_for_rxs(context):
    """ Wait for a ready message to be received from each Rx, then send a
    reply once all Rxs are ready. """
    startup = context.socket(zmq.ROUTER)
    startup.bind("tcp://*:{}".format(TX_STARTUP_PORT))

    # Keep track of the Rx IDs which are ready, mapping each to its address.
    ready_ids = {}

    print("Waiting for ready messages from Rxs...")
    while len(ready_ids) < NUM_RXS:
        address, empty, message = startup.recv_multipart()
        rx_id = message[0]
        print("Rx {} ready.".format(rx_id))
        ready_ids[rx_id - 1] = address

    print("All Rxs ready.")

    # Let the Rxs know the Tx is ready.
    for address in ready_ids.values():
        startup.send_multipart([address, b'', b''])

    startup.close()



def receive_updates(receiver, updates):
    """ Receive any packets available from the receiver socket without blocking,
    storing them in the updates list. """
    while True:
        try:
            message = receiver.recv(flags=zmq.NOBLOCK)
            update = RxUpdate.from_bytes(message)
            updates[update.rx_id - 1].append(update)
            print("Received update: {}".format(update))
        except zmq.ZMQError:
            # No more packets ready to be received.
            return



def check_updates(updates, start_time, loop_start_time):
    """ Check that we have at least one update from each Rx, and that they
    aren't older than the timeout period. If timeout has occurred, raise a
    Timeout"""
    updates_available = True
    for rx_id in range(1, NUM_RXS + 1):
        if len(updates[rx_id - 1]) == 0:
            print("No updates from Rx {} yet.".format(rx_id))
            updates_available = False
            last_update_time = start_time
        else:
            last_update_time = updates[rx_id - 1][-1].timestamp

        if loop_start_time - last_update_time > TIMEOUT_S:
            raise TimeoutException(
                "Timeout occurred. No updates from Rx {} in {} s.".format(
                rx_id, TIMEOUT_S))
    return updates_available


def get_rx_positions(updates):
    """ Return a list of the current Rx positions.

    TODO: Change this if we don't just want to use the most recent updates.
    """
    return [updates[i][-1].rx_coords for i in range(NUM_RXS)]


def swarming_checks(updates, tx_coords, target_location, prev_target_location):
    """ If formation is fine, output the target, otherwise output tx position
    to reset the formation. """
    drones = [tx_coords] + get_rx_positions(updates)
    if (swarming_logic.check_formation(drones)
        and swarming_logic.check_gps(target_location, prev_target_location)):
        # Output target location as the desired location
        desired_location = target_location
    else:
        # Output mothership position as the desired location, to reset formation
        desired_location = tx_coords
        print("RESET FORMATION")
    return desired_location


def perform_multilateration(updates, tx_coords):
    """ Returns the target position estimated by the multilateration module.

    TODO: For now, only use readings from the first 3 Rxs for multilateration.
    Remove this once multilateration works with 4 Rxs.
    TODO: Change this if we don't just want to use the most recent updates.
    """
    num_rxs = 3
    rx_coords = [updates[i][-1].rx_coords for i in range(num_rxs)]
    ranges = [updates[i][-1].range for i in range(num_rxs)]

    return multilateration.estimate_target_position(
        tx_coords, *rx_coords, *ranges)


def plot_positions(tx_coords, updates):
    """ Plot the current positions of the Tx and the Rxs, and the actual
    target position. """
    colors = ['k', 'b', 'g', 'r', 'm']
    positions = [tx_coords] + get_rx_positions(updates)
    for i in range(len(positions)):
        plt.plot(positions[i].long, positions[i].lat, 'x' + colors[i])

    # Get the actual target coords (sent from the Rxs for plotting).
    actual_target_coords = updates[0][-1].target_coords
    plt.plot(actual_target_coords.long, actual_target_coords.lat, 'oc')

    # Call pause to render the changes.
    plt.pause(0.0000001)


def main():
    # Check if we should plot the drone positions on a graph.
    should_plot = "--plot" in sys.argv

    context = zmq.Context()

    wait_for_rxs(context)

    # PULL socket for receiving updates from the Rxs.
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:{}".format(TX_RECEIVE_PORT))

    # PUB socket for sending target position estimates to the Rxs.
    sender = context.socket(zmq.PUB)
    sender.bind("tcp://*:{}".format(TX_SEND_PORT))

    tx_coords = TX_START_COORDS

    # Store all the updates received, with a separate list for each Rx.
    # TODO: also write the updates to a log file?
    updates = [[] for _ in range(NUM_RXS)]

    # Store all the estimated target locations.
    target_locations = []

    start_time = time.time()

    # Create a graph to plot the drone positions if needed.
    if should_plot:
        plt.axis([MIN_LONG, MAX_LONG, MIN_LAT, MAX_LAT])

    while True:
        loop_start_time = time.time()

        receive_updates(receiver, updates)

        updates_available = check_updates(updates, start_time, loop_start_time)

        # If we have an update from each Rx, perform multilateration.
        if updates_available:
            target_coords = perform_multilateration(updates, tx_coords)
            target_locations.append(target_coords)

            # Perform swarming checks, unless this is our first estimation
            # (since we don't have a previous target location yet).
            if len(target_locations) >= 2:
                desired_location = swarming_checks(updates, tx_coords,
                    target_locations[-1], target_locations[-2])
            else:
                desired_location = target_coords

            print("Target Location:", target_coords)
            print("Desired Location:", desired_location)

            # Update our own location
            tx_coords = swarming_logic.update_loc(desired_location, TX_ID)

            # Plot the current Tx, Rx and actual target positions if needed.
            if should_plot:
                plot_positions(tx_coords, updates)

            # Send the desired location and the Tx location to the Rxs.
            update = TxUpdate(desired_location, tx_coords)
            print("Sending update: {}".format(update))
            sender.send(update.to_bytes())

            print()

        # Sleep until it's time to perform multilateration again.
        sleep_time = UPDATE_PERIOD_S - (time.time() - loop_start_time)
        if sleep_time < 0:
            print("Warning: Processing took longer than {} s.".format(
                UPDATE_PERIOD_S))
        else:
            time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        main()
    except TimeoutException as e:
        print(e)
        sys.exit(0)
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")
        sys.exit(0)
