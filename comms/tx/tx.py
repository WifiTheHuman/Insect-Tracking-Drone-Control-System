import time
import zmq
import struct

TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

NUM_RXS = 3

TX_COORDS = (0, 0)


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
            rx_x, rx_y, range_reading = struct.unpack("!iif", message)
            range_readings.append(range_reading)
            rx_coords.append((rx_x, rx_y))
            print("Received reading {}".format(range_reading))

        # TODO: For now use the sum of the ranges as the "target position".
        target_position = sum(range_readings)

        # Publish the target position to the Rxs.
        message = struct.pack("!f", target_position)
        print("Sending target position {}".format(target_position))
        sender.send(message)

        print()


main()
