from unittest import TestCase

from bike.models.frame import (
    Frame,
    Frames
)


class FrameTest(TestCase):

    def test_completeness(self):
        self.assertTrue(Frame(0.0, (1.0, 1.0), (1.0, 1.0, 1.0)).is_complete)
        self.assertFalse(Frame(0.0, (1.0, 1.0), (1.0, 1.0)).is_complete)
        self.assertFalse(Frame(0.0, (1.0, None), (1.0, 1.0, 1.0)).is_complete)
