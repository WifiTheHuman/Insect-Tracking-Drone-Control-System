import struct

from gps import GPSCoord


class RxUpdate:
    def __init__(self, rx_id, timestamp, rx_coords, range_reading):
        self.rx_id = rx_id
        self.timestamp = timestamp
        self.rx_coords = rx_coords
        self.range = range_reading

    def __str__(self):
        return "ID {}, time {}, Rx coords {}, range {}".format(
            self.rx_id, self.timestamp, self.rx_coords, self.range)

    @staticmethod
    def from_bytes(b):
        rx_id, timestamp, lat, lon, range_reading = struct.unpack("!idddd", b)
        return RxUpdate(rx_id, timestamp, GPSCoord(lat, lon), range_reading)

    def to_bytes(self):
        return struct.pack("!idddd", self.rx_id, self.timestamp,
                           self.rx_coords.lat, self.rx_coords.long, self.range)


class TxUpdate:
    def __init__(self, target_coords):
        self.target_coords = target_coords

    def __str__(self):
        return "Target position {}".format(self.target_coords)

    @staticmethod
    def from_bytes(b):
        lat, lon = struct.unpack("!dd", b)
        return TxUpdate(GPSCoord(lat, lon))

    def to_bytes(self):
        return struct.pack("!dd", self.target_coords.lat,
                           self.target_coords.long)
