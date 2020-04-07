import math

# Earth's radius in metres.
EARTH_RADIUS = 6371000


class GPSCoord:
    """ Represents a GPS coordinate with latitude and longitude in
    decimal degrees (DD) format.
    """
    def __init__(self, latitude, longitude):
        self.lat = latitude
        self.long = longitude

    def __str__(self):
        return "({}, {})".format(self.lat, self.long)

    @staticmethod
    def from_nmea(nmea_lat, nmea_long):
        return GPSCoord(GPSCoord.nmea_to_dd(nmea_lat),
                        GPSCoord.nmea_to_dd(nmea_long))

    @staticmethod
    def nmea_to_dd(coord):
        """ Takes a latitude or longitude as a string in NMEA format,
        e.g. "17234.98533E", and converts it to DD."""
        point_index = coord.index(".")
        degrees = int(coord[:point_index - 2])
        minutes = float(coord[point_index - 2:-1])
        direction = coord[-1]

        degrees += minutes / 60
        if direction in ("S", "W"):
            degrees *= -1

        return degrees

    def distance(self, other):
        """ Calculates the distance in meters between two GPS coordinates using
        the equirectangular approximation. """
        lat_1 = math.radians(self.lat)
        lat_2 = math.radians(other.lat)
        long_1 = math.radians(self.long)
        long_2 = math.radians(other.long)
        x = (long_2 - long_1) * math.cos((lat_1 + lat_2) / 2)
        y = lat_2 - lat_1
        distance = math.sqrt(x * x + y * y) * EARTH_RADIUS
        return distance
