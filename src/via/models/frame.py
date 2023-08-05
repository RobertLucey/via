from via.models.generic import GenericObject, GenericObjects
from via.models.gps import GPSPoint


class Frame(GenericObject):
    """
    A single snapshot of data on a journey containing gps, acceleration
    and time info
    """

    def __init__(self, time: float, gps: GPSPoint, acceleration: list):
        """

        :param time:
        :param gps: GPSPoint or dict serialization of GPSPoint
        :param acceleration:
        """
        super().__init__()
        self.time = time
        self.gps = GPSPoint.parse(gps)
        self.acceleration = acceleration

    @staticmethod
    def parse(obj):
        if isinstance(obj, dict):
            return Frame(obj.get("time", None), obj["gps"], obj["acc"])
        if isinstance(obj, Frame):
            return obj
        raise NotImplementedError("Can't parse Frame from type %s" % (type(obj)))

    def distance_from(self, point: GPSPoint) -> float:
        """

        :param point: GPSPoint or tuple of (lat, lng) or Frame object
        :rtype: float
        :return: Distance between points in metres
        """
        if isinstance(point, Frame):
            point = point.gps
        return self.gps.distance_from(point)

    def serialize(self, **kwargs) -> dict:
        data = {"gps": self.gps.serialize(), "acc": self.acceleration}
        if kwargs.get("include_time", True):
            data["time"] = round(self.time, 2)
        return data
