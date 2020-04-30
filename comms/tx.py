import time
import zmq
import struct
import sys

import multilateration
from gps import GPSCoord
from packets import RxUpdate, TxUpdate

TX_STARTUP_PORT = 5554
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

# TODO: This must have the value 3 until the multilateration works with an
# arbitrary number of Rxs.
NUM_RXS = 3

# Tx position is fixed for now. This value must match the one in rx.py
TX_COORDS = GPSCoord(-43.52051, 172.58310)

# How often the Tx should perform multilateration and send an update.
UPDATE_PERIOD_S = 1

# Timeout period for receiving updates from Rxs.
TIMEOUT_S = 3


def receive_updates(receiver, updates):
    """ Receive any packets available from the receiver socket without blocking,
    storing them in the updates list. """
    while True:
        try:
            message = receiver.recv(flags=zmq.NOBLOCK)
            update = RxUpdate.from_bytes(message)
            updates[update.rx_id].append(update)
            print("Received update: {}".format(update))
        except zmq.ZMQError:
            # No more packets ready to be received.
            return


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
        ready_ids[rx_id] = address

    print("All Rxs ready.")

    # Let the Rxs know the Tx is ready.
    for address in ready_ids.values():
        startup.send_multipart([address, b'', b''])

    startup.close()


def main():
    context = zmq.Context()

    wait_for_rxs(context)

    # PULL socket for receiving updates from the Rxs.
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:{}".format(TX_RECEIVE_PORT))

    # PUB socket for sending target position estimates to the Rxs.
    sender = context.socket(zmq.PUB)
    sender.bind("tcp://*:{}".format(TX_SEND_PORT))

    # Store all the updates received, with a separate list for each Rx.
    # TODO: also write the updates to a log file?
    updates = [[] for _ in range(NUM_RXS)]

    start_time = time.time()

    while True:
        loop_start_time = time.time()

        receive_updates(receiver, updates)

        # Check that we have at least one update from each Rx, and that they
        # aren't older than the timeout period.
        updates_available = True
        for rx_id in range(NUM_RXS):
            if len(updates[rx_id]) == 0:
                print("No updates from Rx {} yet.".format(rx_id))
                updates_available = False
                last_update_time = start_time
            else:
                last_update_time = updates[rx_id][-1].timestamp

            if loop_start_time - last_update_time > TIMEOUT_S:
                print(
                    "Timeout occurred. No updates from Rx {} in {} s.".format(
                        rx_id, TIMEOUT_S))
                return

        # If we have an update from each Rx, perform multilateration.
        if updates_available:
            target_coords = multilateration.estimate_target_position(
                TX_COORDS,
                *[update_list[-1].rx_coords for update_list in updates],
                *[update_list[-1].range for update_list in updates])
            update = TxUpdate(target_coords)
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
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")
        sys.exit(0)
