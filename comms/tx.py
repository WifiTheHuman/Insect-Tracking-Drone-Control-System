import time
import zmq
import struct

import multilateration
from gps import GPSCoord

TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

# TODO: This must have the value 3 until the multilateration works with an
# arbitrary number of Rxs.
NUM_RXS = 3

# Tx position is fixed for now. This value must match the one in rx.py
TX_COORDS = GPSCoord(-43.52051, 172.58310)


def main():
    context = zmq.Context()

    # Socket for receiving readings from the Rxs.
    print("Connecting to receiver socket.")
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:{}".format(TX_RECEIVE_PORT))

    # Socket for sending target position estimates to the Rxs.
    print("Connecting to sender socket.")
    sender = context.socket(zmq.PUB)
    sender.bind("tcp://*:{}".format(TX_SEND_PORT))

    while True:
        # Receive one packet from each Rx.
        range_readings = []
        rx_coords = []
        for i in range(NUM_RXS):
            message = receiver.recv()
            rx_lat, rx_long, range_reading = struct.unpack("!ddd", message)
            rx_coord = GPSCoord(rx_lat, rx_long)
            rx_coords.append(rx_coord)
            range_readings.append(range_reading)
            print("Received packet: range {}, Rx coords {}".format(
                range_reading, rx_coord))

        # Estimate the target position and publish it to the Rxs.
        target_coords = multilateration.estimate_target_position(
            TX_COORDS, *rx_coords, *range_readings)
        message = struct.pack("!dd", target_coords.lat, target_coords.long)
        print("Sending target coords {}".format(target_coords))
        sender.send(message)

        print()


main()
