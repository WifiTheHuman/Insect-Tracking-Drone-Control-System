import zmq
import time

# Must match the one in client_gps.py.
PORT = 5556


def main():
    # Socket to send readings to the client.
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(PORT))

    while True:
        time.sleep(1)

        # Change this to readings from the GPS module.
        time_sample = "Sat Aug  3 14:21:15 2019"
        latitude = "4331.23049S"
        longitude = "17234.98533E"

        message = "{},{},{}".format(time_sample, latitude, longitude)
        print("Sending: {}".format(message))
        socket.send(message.encode('utf-8'))


main()
