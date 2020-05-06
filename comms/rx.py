import zmq
import struct
import time
import sys
import threading

from gps import GPSCoord
from packets import RxUpdate, TxUpdate
import swarming_logic

TX_IP_ADDRESS = "localhost"
TX_STARTUP_PORT = 5554
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

TARGET_POSITION_FILENAME = "target_positions_gps.txt"

# For now, the Tx and Rxs are given constant positions, only the target moves.
# These positions are in formation about the first point in target_positions_gps.txt
TX_COORDS = GPSCoord(-43.520508, 172.583089)
RX_COORDS = [
    GPSCoord(-43.520463, 172.583027),
    GPSCoord(-43.520463, 172.583151),
    GPSCoord(-43.520553, 172.583027),
    GPSCoord(-43.520553, 172.583151)
]

# How often the Rx should send updates to the Tx.
UPDATE_PERIOD_S = 1

# Timeout period for receiving updates from the Tx.
TIMEOUT_S = 3


def read_coordinate(file):
    """ Reads the coordinates from the next line of the given file, and returns
    it as a GPSCoord. Each line of the file contains time, latitude and
    longitude in NMEA format.
    """
    time, latitude, longitude = file.readline().split(",")
    return GPSCoord.from_nmea(latitude.strip(), longitude.strip())


def calculate_range(rx, tx, target):
    """ Calculates the range reading in meters as the distance from the Rx to
    the target, plus the distance from the target to the Tx.
    """
    return rx.distance(target) + target.distance(tx)


def sender_loop(context, rx_id):
    # Create a PUSH socket to send updates to the Tx.
    sender = context.socket(zmq.PUSH)
    sender.setsockopt(zmq.LINGER, 0)  # Exit even if there are unsent updates.
    sender.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_RECEIVE_PORT))

    # Create a PAIR socket to communicate with the main thread.
    main_inproc = context.socket(zmq.PAIR)
    main_inproc.connect("inproc://sender")

    target_pos_file = open(TARGET_POSITION_FILENAME)

    rx_coords = RX_COORDS[rx_id - 1]

    while True:
        loop_start_time = time.time()

        # Check if the main thread wants us to terminate.
        try:
            main_inproc.recv(flags=zmq.NOBLOCK)
            print("Sender thread exiting.")
            return
        except zmq.ZMQError:
            pass

        # Get the next target position from the file.
        target_coords = read_coordinate(target_pos_file)
        print("Expected target coords {}".format(target_coords))

        # Send an update containing the Rx position and range.
        range_reading = calculate_range(rx_coords, TX_COORDS, target_coords)
        update = RxUpdate(rx_id, time.time(), rx_coords, range_reading)
        print("Sending update: {}".format(update))
        sender.send(update.to_bytes())

        # Sleep until it's time to send another update.
        sleep_time = UPDATE_PERIOD_S - (time.time() - loop_start_time)
        if sleep_time < 0:
            print("Warning: Sending update took longer than {} s.".format(
                UPDATE_PERIOD_S))
        else:
            time.sleep(sleep_time)


def receiver_loop(context, rx_id):
    # Create a SUB socket to receive updates from the Tx.
    receiver = context.socket(zmq.SUB)
    receiver.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_SEND_PORT))
    receiver.setsockopt_string(zmq.SUBSCRIBE, "")  # TODO: change this?

    # Create a PAIR socket to communicate with the main thread.
    main_inproc = context.socket(zmq.PAIR)
    main_inproc.connect("inproc://receiver")

    # Poller to wait for messages from the Tx or the main thread.
    poller = zmq.Poller()
    poller.register(receiver, zmq.POLLIN)
    poller.register(main_inproc, zmq.POLLIN)

    while True:
        sockets = dict(poller.poll(timeout=TIMEOUT_S * 1000))
        if main_inproc in sockets:
            # The main thread has sent a termination request.
            print("Receiver thread exiting.")
            return
        if receiver in sockets:
            # Received an update from the Tx.
            update = TxUpdate.from_bytes(receiver.recv())
            print("Received update: {}".format(update))
            desired_location = swarming_logic.update_loc(update.target_coords, rx_id)
            print("Desired location: {}".format(desired_location))
            print()
        else:
            print("Timeout occurred. No updates from Tx in {} s".format(
                TIMEOUT_S))
            # Tell the main thread that the process should terminate.
            main_inproc.send(b"")


def wait_for_tx(context, rx_id):
    """ Send the Tx a ready message containg the Rx's ID, then wait for a
    response. """
    startup = context.socket(zmq.REQ)
    startup.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_STARTUP_PORT))
    startup.send(bytes([rx_id]))

    print("Waiting for ready message from Tx...")
    startup.recv()
    startup.close()
    print("Tx ready.")


def main():
    if len(sys.argv) != 2:
        print("Usage: {} <rx-id>".format(sys.argv[0]))
        sys.exit(1)

    # TODO: For now, Rx position is constant and determined by the given ID.
    try:
        rx_id = int(sys.argv[1])
        assert (rx_id in range(1, len(RX_COORDS) + 1))
    except:
        print(
            "rx-id must be an integer from 1 to {}".format(len(RX_COORDS)))
        sys.exit(1)

    context = zmq.Context()

    wait_for_tx(context, rx_id)

    # Create a thread to send updates, and a PAIR socket to communicate with it.
    sender = threading.Thread(target=sender_loop, args=(context, rx_id))
    sender_inproc = context.socket(zmq.PAIR)
    sender_inproc.bind("inproc://sender")

    # Create a thread to receive updates, and a PAIR socket to communicate with it.
    receiver = threading.Thread(target=receiver_loop, args=(context, rx_id))
    receiver_inproc = context.socket(zmq.PAIR)
    receiver_inproc.bind("inproc://receiver")

    # Poller to wait for messages from the threads.
    poller = zmq.Poller()
    poller.register(sender_inproc, zmq.POLLIN)
    poller.register(receiver_inproc, zmq.POLLIN)

    # Start the threads.
    sender.start()
    receiver.start()

    # Wait for one of the threads to request termination, or for an interrupt.
    try:
        poller.poll()
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")

    # Tell each of the threads to terminate.
    sender_inproc.send(b"")
    receiver_inproc.send(b"")

    sender.join()
    receiver.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")
        sys.exit(0)
