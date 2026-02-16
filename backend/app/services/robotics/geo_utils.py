import numpy as np
import math

class GeoUtils:
    EARTH_RADIUS = 6371000.0  # meters

    @staticmethod
    def latlon_to_xy(lat, lon, ref_lat, ref_lon):
        """
        Convert (lat, lon) to (x, y) in meters relative to (ref_lat, ref_lon).
        Using simple flat-earth approximation for small areas.
        x: Easting
        y: Northing
        """
        d_lat = math.radians(lat - ref_lat)
        d_lon = math.radians(lon - ref_lon)

        ref_lat_rad = math.radians(ref_lat)

        x = d_lon * GeoUtils.EARTH_RADIUS * math.cos(ref_lat_rad)
        y = d_lat * GeoUtils.EARTH_RADIUS

        return x, y

    @staticmethod
    def xy_to_latlon(x, y, ref_lat, ref_lon):
        """
        Convert local (x, y) meters to (lat, lon) relative to (ref_lat, ref_lon).
        """
        ref_lat_rad = math.radians(ref_lat)

        d_lat = y / GeoUtils.EARTH_RADIUS
        d_lon = x / (GeoUtils.EARTH_RADIUS * math.cos(ref_lat_rad))

        lat = ref_lat + math.degrees(d_lat)
        lon = ref_lon + math.degrees(d_lon)

        return lat, lon
