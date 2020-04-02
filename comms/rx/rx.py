import zmq
import struct
import time
import sys

TX_IP_ADDRESS = "localhost"
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

TARGET_POSITION_FILENAME = "target_positions.txt"

TX_COORDS = (0, 0)


def distance(p1, p2):
    """ Calculates the Euclidean distance between two points. """
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5


def calculate_range(rx, tx, target):
    """ Calculates the range reading as the distance from the Rx to the
        target, plus the distance from the target to the Tx.
    """
    return distance(rx, target) + distance(target, tx)


def construct_packet(rx_coords, range_reading):
    """ Constructs a packet containing the current position of the Rx and the
        range reading. Returns the packet as a bytes object.
    """
    x, y = rx_coords
    return struct.pack("!iif", x, y, range_reading)


def main():
    # TODO: For now, Rx position is constant and given as a command-line arg.
    if len(sys.argv) != 3:
        print("Usage: {} <x-coord> <y-coord>".format(sys.argv[0]))
        sys.exit(1)

    rx_coords = int(sys.argv[1]), int(sys.argv[2])

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
        target_x, target_y = target_pos_file.readline().split(",")
        target_coords = int(target_x), int(target_y)
        range_reading = calculate_range(rx_coords, TX_COORDS, target_coords)
        message = construct_packet(rx_coords, range_reading)

        print("Sending range reading {}".format(range_reading))
        sender.send(message)

        #  Wait for the Tx to respond with an estimated target position.
        message = receiver.recv()
        target_position, = struct.unpack("!f", message)
        print("Received target position {}".format(target_position))

        print()


main()
