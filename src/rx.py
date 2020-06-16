import zmq
import time
import sys
import argparse

from gps import GPSCoord
from packets import RxUpdate, TxUpdate
import swarming_logic

TX_IP_ADDRESS = "localhost"

# Must match the port numbers in tx.py
TX_STARTUP_PORT = 5554
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

TARGET_POSITION_FILENAME = "target_positions_gps.txt"

# Tx starting position. This value must match the one in tx.py
TX_START_COORDS = GPSCoord(-43.520508, 172.583089)

# This must match the value in tx.py, and be compatible with the swarming logic
# and the multilateration.
NUM_RXS = 4

# Rx starting positions, length must be equal to NUM_RXs.
# The Rx with ID 1 is assigned the first position in the list, and so on.
RX_START_COORDS = [
    GPSCoord(-43.520463, 172.583027),
    GPSCoord(-43.520463, 172.583151),
    GPSCoord(-43.520553, 172.583027),
    GPSCoord(-43.520553, 172.583151)
]

# How often the Rx should send updates to the Tx.
UPDATE_PERIOD_S = 1

# Timeout period for receiving updates from the Tx.
TIMEOUT_S = 3

# How often the main loop runs. This determines the timing accuracy in sending
# updates.
LOOP_PERIOD_MS = 1


class TimeoutException(Exception):
    pass


def wait_for_tx(context, rx_id):
    """ Send the Tx a ready message containg the Rx ID and wait for a response. """
    startup = context.socket(zmq.REQ)
    startup.setsockopt(zmq.LINGER, 0)  # Exit if startup process is interrupted.
    startup.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_STARTUP_PORT))
    startup.send(bytes([rx_id]))

    print("Waiting for ready message from Tx...")
    startup.recv()
    startup.close()
    print("Tx ready.")


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


def receive_update(rx_id, socket):
    """ Receive an update from the Tx, and return the new desired location of
    this Rx, and the current position of the Tx.
    """
    # Called when socket is ready for reading, so non-blocking recv can be used.
    update = TxUpdate.from_bytes(socket.recv(flags=zmq.NOBLOCK))
    print("Received update: {}".format(update))

    # Calculate the desired location for this Rx based on the swarming logic.
    desired_location = swarming_logic.update_loc(update.target_coords, rx_id)
    print("Rx {} desired location: {}".format(rx_id, desired_location))

    print()

    return desired_location, update.tx_coords


def send_update(rx_id, socket, target_pos_file, rx_coords, tx_coords):
    """ Send an update to the Tx containing the Rx position and range. """
    # Get the next target position from the file.
    target_coords = read_coordinate(target_pos_file)
    print("Expected target coords {}".format(target_coords))

    # Calculate the emulated range based on the Rx, Tx and target positions.
    range_reading = calculate_range(rx_coords, tx_coords, target_coords)

    # TODO: For now, also send the actual target coordinates so the Tx can plot
    # them. Remove this when no longer needed.
    update = RxUpdate(rx_id, time.time(), rx_coords, range_reading,
                      target_coords)
    socket.send(update.to_bytes())
    print("Sending update: {}".format(update))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rx_id', type=int, choices=range(1, NUM_RXS + 1))
    rx_id = parser.parse_args().rx_id

    context = zmq.Context()

    # Tell the Tx that this Rx is ready, and wait for it to respond.
    wait_for_tx(context, rx_id)

    # Create a PUSH socket to send updates to the Tx.
    sender = context.socket(zmq.PUSH)
    sender.setsockopt(zmq.LINGER, 0)  # Exit even if there are unsent updates.
    sender.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_RECEIVE_PORT))

    # Create a SUB socket to receive updates from the Tx.
    receiver = context.socket(zmq.SUB)
    receiver.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_SEND_PORT))
    receiver.setsockopt_string(zmq.SUBSCRIBE, "")  # TODO: change this?

    # Current position of this Rx, initialised to its hard-coded start position,
    # then updated to the new desired position output by the swarming logic.
    # TODO: Eventually this will be the real coordinates read from a GPS module.
    rx_coords = RX_START_COORDS[rx_id - 1]

    # Current position of the Tx, initialised to its hard-coded start position,
    # then updated when the Tx sends updates containing its position.
    # TODO: This is used for calculating emulated range readings, so won't be
    # necessary once real ranges are received from the radar.
    tx_coords = TX_START_COORDS

    # File containing the coordinates of the emulated target path.
    target_pos_file = open(TARGET_POSITION_FILENAME)

    # Last time an update from the Tx was received, to check for timeout.
    last_update_received_time = time.time()

    # Last time an update was sent to the Tx, to check if its time to send another.
    last_update_sent_time = time.time()

    # Poller required to set a timeout on receiving from the receiver socket.
    poller = zmq.Poller()
    poller.register(receiver, zmq.POLLIN)

    while True:
        sockets = dict(poller.poll(timeout=LOOP_PERIOD_MS))
        if receiver in sockets:
            # Update Rx and Tx positions based on received update.
            rx_coords, tx_coords = receive_update(rx_id, receiver)
            last_update_received_time = time.time()
        else:
            # Didn't receive an update from the Tx, check if timeout occurred.
            if time.time() >= last_update_received_time + TIMEOUT_S:
                raise TimeoutException(
                    "Timeout occurred. No updates from Tx in {} s.".format(
                        TIMEOUT_S))

        # Check if it's time to send an update
        if time.time() >= last_update_sent_time + UPDATE_PERIOD_S:
            send_update(rx_id, sender, target_pos_file, rx_coords, tx_coords)
            last_update_sent_time = time.time()


if __name__ == "__main__":
    try:
        main()
    except TimeoutException as e:
        print(e)
        sys.exit(0)
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")
        sys.exit(0)
