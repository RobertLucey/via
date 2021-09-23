from unittest import TestCase, skip

from via.models.frame import (
    Frame,
    Frames
)


class FrameTest(TestCase):

    def test_completeness(self):
        self.assertTrue(Frame(0.0, {'lat': 0.1, 'lng': 1.0}, 1.0).is_complete)
        self.assertFalse(Frame(0.0, {'lat': 0.0, 'lng': None}, 1.0).is_complete)

    def test_lat(self):
        self.assertEqual(
            Frame(
                0.0,
                {'lat': 0.0, 'lng': 1.0},
                1.0
            ).gps.lat,
            0
        )

    def test_lng(self):
        self.assertEqual(
            Frame(
                0.0,
                {'lat': 0.0, 'lng': 1.0},
                1.0
            ).gps.lng,
            1
        )

    def test_distance_from_point(self):
        frame_1 = Frame(
            0.0,
            {'lat': 0.0, 'lng': 0.0},
            1.0
        )
        frame_2 = Frame(
            0.0,
            {'lat': 0.0, 'lng': 1.0},
            1.0
        )
        self.assertTrue(111500 > frame_1.distance_from(frame_2) > 111000)
        self.assertTrue(111500 > frame_1.distance_from(frame_2.gps) > 111000)

    def test_serialize(self):
        self.assertEqual(
            Frame(0.0, {'lat': 0.0, 'lng': 1.0}, [1.0, 2.0, 3.0]).serialize(),
            {
                'time': 0.0,
                'gps': {'lat': 0.0, 'lng': 1.0, 'elevation': None},
                'acc': [1.0, 2.0, 3.0]
            }
        )

    def test_parse(self):
        frame = Frame(
            0.0,
            {'lat': 0.0, 'lng': 1.0},
            (1.0, 2.0, 3.0)
        )
        self.assertEqual(Frame.parse(frame).serialize(), frame.serialize())
        self.assertEqual(
            Frame.parse({'time': 0.0, 'gps': {'lat': 0.0, 'lng': 1.0}, 'acc': (1.0, 2.0, 3.0)}).serialize(),
            frame.serialize()
        )
        with self.assertRaises(NotImplementedError):
            Frame.parse(None)


class FramesTest(TestCase):

    def setUp(self):
        self.frames = Frames()
        self.frames.append(
            Frame(
                0.0,
                {'lat': 0.0, 'lng': 1.0},
                (1.0, 2.0, 3.0)
            )
        )
        self.frames.append(
            Frame(
                1.0,
                {'lat': 2.0, 'lng': 3.0},
                (1.0, 2.0, 3.0)
            )
        )

    def test_most_directional(self):
        self.assertEqual(
            self.frames.most_northern,
            2
        )
        self.assertEqual(
            self.frames.most_southern,
            0
        )
        self.assertEqual(
            self.frames.most_eastern,
            3
        )
        self.assertEqual(
            self.frames.most_western,
            1
        )

    @skip('todo')
    def test_quality(self):
        pass
