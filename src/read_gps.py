import serial
from gps import GPSCoord


GPGGA = '$GPGGA'


def main():

	ser = serial.Serial('../../../../../../../dev/tty.usbserial', 4800, timeout=5)
	line = ser.readline()	# Read remaining junk line so that next line is clean

	while True:
		try:
			line = ser.readline().decode('utf-8')
			splitline = line.split(",")

			if splitline[0] == GPGGA:
				latitude_nmea = splitline[2] + splitline[3]
				longitude_nmea = splitline[4] + splitline[5]
				coord = GPSCoord.from_nmea(latitude_nmea, longitude_nmea)

				print(coord)
		except UnicodeDecodeError:
			print("Failed to decode")
			continue

main()