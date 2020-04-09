import zmq
import struct
import time
import sys

from gps import GPSCoord

TX_IP_ADDRESS = "localhost"
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

TARGET_POSITION_FILENAME = "target_positions_gps.txt"

# For now, the Tx and Rxs are given constant positions, only the target moves.
TX_COORDS = GPSCoord(-43.52051, 172.58310)
RX_COORDS = [
    GPSCoord(-43.52046, 172.58305),
    GPSCoord(-43.52046, 172.58310),
    GPSCoord(-43.52056, 172.58305),
]


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


def main():
    # TODO: For now, Rx position is constant and determined by the given ID.
    if len(sys.argv) != 2:
        print("Usage: {} <rx-id>".format(sys.argv[0]))
        sys.exit(1)

    try:
        rx_id = int(sys.argv[1])
        assert (rx_id in range(len(RX_COORDS)))
        rx_coords = RX_COORDS[rx_id]
    except:
        print(
            "rx-id must be an integer from 0 to {}".format(len(RX_COORDS) - 1))
        sys.exit(1)

    context = zmq.Context()

    # Socket to send readings to the Tx.
    print("Connecting sender socket.")
    sender = context.socket(zmq.PUSH)
    sender.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_RECEIVE_PORT))

    # Socket to receive target position estimates from the Tx.
    print("Connecting receiver socket.")
    receiver = context.socket(zmq.SUB)
    receiver.connect("tcp://{}:{}".format(TX_IP_ADDRESS, TX_SEND_PORT))
    receiver.setsockopt_string(zmq.SUBSCRIBE, "")  # TODO

    target_pos_file = open(TARGET_POSITION_FILENAME)

    while True:
        time.sleep(1)

        # Send the Rx position and range reading to the Tx.
        target_coords = read_coordinate(target_pos_file)
        range_reading = calculate_range(rx_coords, TX_COORDS, target_coords)
        message = struct.pack("!ddd", rx_coords.lat, rx_coords.long,
                              range_reading)
        print("Sending packet: range {}, Rx coords {}".format(
            range_reading, rx_coords))
        sender.send(message)

        #  Wait for the Tx to respond with an estimated target position.
        message = receiver.recv()
        received_target_coords = GPSCoord(*struct.unpack("!dd", message))
        print("Received target coords {}".format(received_target_coords))
        print("Expected target coords {}".format(target_coords))

        print()


main()
