import time
import zmq
import sys
import matplotlib.pyplot as plt
import argparse

import multilateration
import swarming_logic
from gps import GPSCoord
from packets import RxUpdate, TxUpdate

# Must match the port numbers in rx.py
TX_STARTUP_PORT = 5554
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

# This must match the value in rx.py, and be compatible with the swarming logic
# and the multilateration.
NUM_RXS = 4

# Tx starting position. This value must match the one in rx.py
TX_START_COORDS = GPSCoord(-43.520508, 172.583089)

# Latitude and logtitude limits for the expected drone and target coordinates.
# Used to define the boundaries of the plot.
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
    reply once all Rxs are ready.
    """
    startup = context.socket(zmq.ROUTER)
    startup.bind("tcp://*:{}".format(TX_STARTUP_PORT))

    # Keep track of the Rx IDs which are ready.
    # Each ID is mapped to its address, so that the Tx can send a response to
    # the same addresses once all Rxs are ready.
    ready_ids = {}

    print("Waiting for ready messages from Rxs...")
    while len(ready_ids) < NUM_RXS:
        address, empty, message = startup.recv_multipart()
        # The ready message is a single byte containing the Rx ID.
        rx_id = message[0]
        ready_ids[rx_id - 1] = address
        print("Rx {} ready.".format(rx_id))

    print("All Rxs ready.")

    # Let the Rxs know the Tx is ready (with an empty message).
    for address in ready_ids.values():
        startup.send_multipart([address, b'', b''])

    startup.close()


def receive_initial_updates(receiver, updates):
    """ Receive updates until there is at least one from each Rx. raising a
    TimeoutException if this takes longer than the timeout period.
    """
    start_time = time.time()

    while not all(len(update_list) > 0 for update_list in updates):
        receive_updates(receiver, updates)
        if time.time() > start_time + TIMEOUT_S:
            raise TimeoutException(
                "Timeout waiting for initial updates from every Rx")


def receive_updates(receiver, updates):
    """ Receive any packets available from the receiver socket without blocking,
    storing them in the updates list.
    """
    while True:
        try:
            message = receiver.recv(flags=zmq.NOBLOCK)
            update = RxUpdate.from_bytes(message)
            updates[update.rx_id - 1].append(update)
            print("Received update: {}".format(update))
        except zmq.ZMQError:
            # No more packets ready to be received.
            return


def check_for_timeout(updates):
    """ Check that we have an update from each Rx which is more recent than the
    timeout period. If timeout has occurred, raise a TimeoutException.
    """
    for rx_id in range(1, NUM_RXS + 1):
        last_update_time = updates[rx_id - 1][-1].timestamp

        if time.time() > last_update_time + TIMEOUT_S:
            raise TimeoutException(
                "Timeout occurred. No updates from Rx {} in {} s.".format(
                    rx_id, TIMEOUT_S))


def perform_multilateration(updates, tx_coords):
    """ Returns the target position estimated by the multilateration module.

    TODO: For now, only use readings from the first 3 Rxs for multilateration.
    Remove this once multilateration works with 4 Rxs.
    TODO: Change this if we don't just want to use the most recent updates.
    """
    num_rxs = 3
    rx_coords = [updates[i][-1].rx_coords for i in range(num_rxs)]
    ranges = [updates[i][-1].range for i in range(num_rxs)]

    return multilateration.estimate_target_position(tx_coords, *rx_coords,
                                                    *ranges)


def get_rx_positions(updates):
    """ Return a list of the current Rx positions.

    TODO: Change this if we don't just want to use the most recent updates.
    """
    return [updates[i][-1].rx_coords for i in range(NUM_RXS)]


def swarming_checks(tx_coords, rx_positions, target_coords,
                    previous_target_coords):
    """ Return the desired centre position of the formation. If formation is
    fine, output the target position, otherwise output the Tx position to reset
    the formation.
    """
    if (swarming_logic.check_formation([tx_coords] + rx_positions) and
            swarming_logic.check_gps(target_coords, previous_target_coords)):
        # Output target position as the desired centre position.
        return target_coords
    else:
        # Output mothership position as the desired centre position, to reset
        # the formation.
        print("RESET FORMATION")
        return tx_coords


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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p',
        '--plot',
        action='store_true',
        help='plots the drone and target positions on a graph during execution'
    )
    should_plot = parser.parse_args().plot

    context = zmq.Context()

    wait_for_rxs(context)

    # PULL socket for receiving updates from the Rxs.
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:{}".format(TX_RECEIVE_PORT))

    # PUB socket for sending target position estimates to the Rxs.
    sender = context.socket(zmq.PUB)
    sender.bind("tcp://*:{}".format(TX_SEND_PORT))

    # Current position of the Tx, initialised to its hard-coded start position,
    # then updated based on the desired location output by the swaming logic.
    # TODO: Eventually this will be the real position read from a GPS module.
    tx_coords = TX_START_COORDS

    # Store all the updates received, with a separate list for each Rx.
    # TODO: only store updates temporarily then write them to a log file?
    updates = [[] for _ in range(NUM_RXS)]

    # Create a graph to plot the drone and target positions, if necessary.
    if should_plot:
        plt.axis([MIN_LONG, MAX_LONG, MIN_LAT, MAX_LAT])

    # Wait until at least one update is received from each Rx.
    receive_initial_updates(receiver, updates)

    # Store all the estimated target positions.
    # Perform an initial multilateration, so that the swarming checks have a
    # previous target position to compare against.
    # TODO: only store positions temporarily then write them to a log file?
    target_positions = [perform_multilateration(updates, tx_coords)]

    while True:
        loop_start_time = time.time()

        receive_updates(receiver, updates)
        check_for_timeout(updates)

        target_coords = perform_multilateration(updates, tx_coords)
        target_positions.append(target_coords)

        desired_centre_position = swarming_checks(tx_coords,
                                                  get_rx_positions(updates),
                                                  target_positions[-1],
                                                  target_positions[-2])

        print("Estimated target position:", target_coords)
        print("Desired formation centre:", desired_centre_position)

        # Update the Tx's own position.
        tx_coords = swarming_logic.update_loc(desired_centre_position, TX_ID)

        # Plot the current Tx, Rx and actual target positions if needed.
        if should_plot:
            plot_positions(tx_coords, updates)

        # Send the desired centre position and the Tx position to the Rxs.
        update = TxUpdate(desired_centre_position, tx_coords)
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
