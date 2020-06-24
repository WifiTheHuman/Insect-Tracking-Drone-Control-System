import zmq
import time
import serial
from gps import GPSCoord


# Must match the one in client_gps.py.
PORT = 5556


def main():
    # Socket to send readings to the client.
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(PORT))

    storage = open("gps_storage.txt", "r")
    gps_data = storage.readlines()

    for line in gps_data:

        # Change this to readings from the GPS module.
        # time_sample = "Sat Aug  3 14:21:15 2019"
        # latitude = "4331.23049S"
        # longitude = "17234.98533E"
        splitline = line.split(",")

        time_sample = splitline[0]
        latitude_str = splitline[1]
        longitude_str = splitline[2]
        coord = GPSCoord(float(latitude_str), float(longitude_str))

        print_message = "{},{:.5f},{:.5f}".format(time_sample, coord.lat, coord.long)
        message = "{},{:.5f},{:.5f}".format(time_sample, coord.lat, coord.long)
        print("Sending: {}".format(print_message))
        socket.send(message.encode('utf-8'))
        time.sleep(1)

    storage.close()

main()
