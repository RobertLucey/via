import busio

import adafruit_gps

from bike.utils import (
    timing,
    get_board
)
from bike.models.gps import GPSPoint

board = get_board()


class GPSInterface():

    def __init__(
        self,
        TX=board.TX,
        RX=board.RX,
        baudrate=9600,
        timeout=30,
        debug=False
    ):
        """

        :kwarg TX:
        :kwarg RX:
        :kwarg baudrate:
        :kwarg timeout:
        :kwarg debug:
        """
        self.interface = self.get_interface(TX, RX, baudrate, timeout, debug)
        self.interface.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        self.interface.send_command(b'PMTK220,1000')

    def get_interface(self, TX, RX, baudrate, timeout, debug):
        uart = busio.UART(
            TX,
            RX,
            baudrate=baudrate,
            timeout=timeout
        )

        return adafruit_gps.GPS(
            uart,
            debug=debug
        )

    @timing
    def get_lat_lng(self):

        # In example the update is done at top of this def
        self.interface.update()
        if not self.interface.has_fix:
            return GPSPoint(None, None, elevation=None)

        return GPSPoint(
            self.interface.latitude,
            self.interface.longitude,
            elevation=None
        )
