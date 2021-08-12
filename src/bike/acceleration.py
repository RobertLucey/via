import adafruit_lis331

from bike.utils import (
    timing,
    get_board
)

board = get_board()


class AccelerometerInterface():

    def __init__(self):

        # TODO: might want to put on a high pass filter

        self.interface = self.get_interface()

    def get_interface():

        i2c = board.I2C()

        # uncomment this line and comment out the one after if using the H3LIS331
        # lis = adafruit_lis331.H3LIS331(i2c)
        return adafruit_lis331.LIS331HH(i2c)

    @timing
    def get_acceleration(self):
        return sum(self.interface.acceleration)  # FIXME: this is bad
