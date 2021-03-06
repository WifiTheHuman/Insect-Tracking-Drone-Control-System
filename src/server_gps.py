import zmq
import time
import serial
from gps import GPSCoord


# Must match the one in client_gps.py.
PORT = 5556

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
GPGGA = '$GPGGA'

def init_socket():
    # Socket to send readings to the client.
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(PORT))
    return socket

def main():
    # Socket to send readings to the client.
    socket = init_socket()

    ser = serial.Serial('../../../../../../../dev/tty.usbserial', 4800, timeout=5)
    line = ser.readline()   # Read remaining junk line so that next line is clean

    while True:

        # Change this to readings from the GPS module.
        # time_sample = "Sat Aug  3 14:21:15 2019"
        # latitude = "4331.23049S"
        # longitude = "17234.98533E"
        line = ser.readline().decode('utf-8')
        splitline = line.split(",")

        if splitline[0] == GPGGA:
            date = time.localtime(time.time())
            gps_time = "{}:{}:{}".format(splitline[1][:2], splitline[1][2:4], splitline[1][4:-4])
            time_sample = "{} {}  {} {} {}".format(WEEKDAYS[date.tm_wday], MONTHS[date.tm_mon-1], 
                date.tm_mday, gps_time, date.tm_year)
            latitude_nmea = splitline[2] + splitline[3]
            longitude_nmea = splitline[4] + splitline[5]
            coord = GPSCoord.from_nmea(latitude_nmea, longitude_nmea)

            print_message = "{},{:.5f},{:.5f}".format(time_sample, coord.lat, coord.long)
            message = "{},{:.5f},{:.5f}".format(time_sample, coord.lat, coord.long)
            storage = open("gps_storage.txt","w")
            storage.write(message + '\n')
            print("Sending: {}".format(print_message))

            # Send new gps data to NUC
            socket.send(message.encode('utf-8'))


main()
