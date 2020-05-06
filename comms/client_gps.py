import zmq

# Will need to change this if communicating between different machines.
IP_ADDRESS = "localhost"

# Must match the one in server_gps.py
PORT = 5556


def main():
    # Socket receive readings from the server.
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://{}:{}".format(IP_ADDRESS, PORT))
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    while True:
        message = socket.recv().decode('utf-8')
        time_sample, latitude, longitude = message.split(',')
        print("time_sample: {}, latitude: {}, longtitude: {}".format(
            time_sample, latitude, longitude))

        messagedata = time_sample + ',' + latitude + ',' + longitude
        fichier=open("data_gps.txt", "w")
        storage=open("data_storage.txt","a")
        fichier.write(messagedata + '\n')
        storage.write(messagedata + '\n')
        fichier.close()


main()
