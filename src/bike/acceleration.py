import board
import adafruit_lis331

from bike.utils import timing


class AcceleratorInterface():

    def __init__(self):

        i2c = board.I2C()

        # uncomment this line and comment out the one after if using the H3LIS331
        # lis = adafruit_lis331.H3LIS331(i2c)
        self.interface = adafruit_lis331.LIS331HH(i2c)

    @timing
    def get_acceleration(self):
        return self.interface.acceleration
