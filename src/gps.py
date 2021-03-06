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
        return "({:.6f}, {:.6f})".format(self.lat, self.long)

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
        x = self.x_distance(other)
        y = self.y_distance(other)
        return math.sqrt(x * x + y * y)

    def x_distance(self, other):
        """ Calculates the x component of the distance in meters between two GPS
        coordinates using the equirectangular approximation. """
        lat_1 = math.radians(self.lat)
        lat_2 = math.radians(other.lat)
        long_1 = math.radians(self.long)
        long_2 = math.radians(other.long)
        x = (long_2 - long_1) * math.cos((lat_1 + lat_2) / 2)
        return x * EARTH_RADIUS

    def y_distance(self, other):
        """ Calculates the y component of the distance in meters between two GPS
        coordinates using the equirectangular approximation. """
        lat_1 = math.radians(self.lat)
        lat_2 = math.radians(other.lat)
        y = lat_2 - lat_1
        return y * EARTH_RADIUS

    def add_x_offset(self, x):
        """ Returns a new GPSCoord with the given offset x in meters added to
        the longitude. """
        delta_long_rad = x / EARTH_RADIUS / math.cos(math.radians(self.lat))
        new_long = self.long + math.degrees(delta_long_rad)
        return GPSCoord(self.lat, new_long)

    def add_y_offset(self, y):
        """ Returns a new GPSCoord with the given offset y in meters added to
        the latitude. """
        delta_lat_rad = y / EARTH_RADIUS
        new_lat = self.lat + math.degrees(delta_lat_rad)
        return GPSCoord(new_lat, self.long)
