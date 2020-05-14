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
    def __init__(self, target_coords, tx_coords):
        self.target_coords = target_coords
        # TODO: for now, the Tx sends it's own coordinates to the Rx as well,
        # for use in calculating the range based on an emulated target position.
        self.tx_coords = tx_coords

    def __str__(self):
        return "Target position {}, Tx coords {}".format(
            self.target_coords, self.tx_coords)

    @staticmethod
    def from_bytes(b):
        target_lat, target_long, tx_lat, tx_long = struct.unpack("!dddd", b)
        return TxUpdate(GPSCoord(target_lat, target_long),
                        GPSCoord(tx_lat, tx_long))

    def to_bytes(self):
        return struct.pack("!dddd", self.target_coords.lat,
            self.target_coords.long, self.tx_coords.lat, self.tx_coords.long)
