from unittest import TestCase

from via.models.point import FramePoint, FramePoints, Context


class FramePointTest(TestCase):
    def test_parse(self):
        self.assertEqual(
            FramePoint.parse(
                {"time": 10, "gps": {"lat": 1, "lng": 2}, "acc": [1, 2, 3, 4]}
            ).serialize(),
            {
                "acc": [1, 2, 3, 4],
                "context": {"post": [], "pre": []},
                "gps": {"elevation": None, "lat": 1, "lng": 2},
                "time": 10,
                "slow": False,
            },
        )

        self.assertEqual(
            FramePoint.parse(
                FramePoint.parse(
                    {"time": 10, "gps": {"lat": 1, "lng": 2}, "acc": [1, 2, 3, 4]}
                )
            ).serialize(),
            {
                "acc": [1, 2, 3, 4],
                "context": {"post": [], "pre": []},
                "gps": {"elevation": None, "lat": 1, "lng": 2},
                "time": 10,
                "slow": False,
            },
        )

    def test_speed_no_context(self):
        no_context = FramePoint.parse(
            {"time": 10, "gps": {"lat": 1, "lng": 1}, "acc": [1, 2, 3, 4]}
        )
        self.assertEqual(no_context.speed, None)

    def test_speed_context_no_movement(self):
        pre_context = [
            FramePoint.parse(
                {"time": 10, "gps": {"lat": 1, "lng": 1}, "acc": [1, 2, 3, 4]}
            )
        ]
        post_context = [
            FramePoint.parse(
                {"time": 30, "gps": {"lat": 1, "lng": 1}, "acc": [1, 2, 3, 4]}
            )
        ]

        with_context = FramePoint.parse(
            {"time": 20, "gps": {"lat": 1, "lng": 1}, "acc": [1, 2, 3, 4]}
        )
        with_context.set_context(pre=pre_context, post=post_context)
        self.assertEqual(with_context.speed, 0)

    def test_speed_context_movement(self):
        pre_context = [
            FramePoint.parse(
                {"time": 10, "gps": {"lat": 1, "lng": 1}, "acc": [1, 2, 3, 4]}
            )
        ]
        post_context = [
            FramePoint.parse(
                {"time": 30, "gps": {"lat": 1.2, "lng": 1.2}, "acc": [1, 2, 3, 4]}
            )
        ]

        with_context = FramePoint.parse(
            {"time": 20, "gps": {"lat": 1.1, "lng": 1.1}, "acc": [1, 2, 3, 4]}
        )
        with_context.set_context(pre=pre_context, post=post_context)
        self.assertEqual(with_context.speed, 1572.39)

    def test_slow(self):
        pass

    def test_get_edges_with_context(self):
        pass

    def test_get_best_edge(self):
        pass

    def test_append_acceleration(self):
        pass

    def test_speed_between(self):
        pass

    def test_distance_from(self):
        pass

    def test_is_complete(self):
        pass

    def test_road_quality(self):
        pass

    def test_serialize(self):
        pass

    def test_gps_hash(self):
        pass

    def test_content_hash(self):
        self.assertEqual(
            FramePoint.parse(
                {"time": 10, "gps": {"lat": 1, "lng": 1}, "acc": [1, 2, 3, 4]}
            ).serialize(),
            {
                "slow": False,
                "time": 10,
                "gps": {"lat": 1, "lng": 1, "elevation": None},
                "acc": [1, 2, 3, 4],
                "context": {"post": [], "pre": []},
            },
        )


class FramePointsTest(TestCase):
    def test_get_multi_point(self):
        points = FramePoints()
        points.append(
            FramePoint.parse(
                {"time": 10, "gps": {"lat": 1, "lng": 2}, "acc": [1, 2, 3, 4]}
            )
        )
        points.append(
            FramePoint.parse(
                {"time": 20, "gps": {"lat": 3, "lng": 4}, "acc": [1, 2, 3, 4]}
            )
        )
        points.append(
            FramePoint.parse(
                {"time": 30, "gps": {"lat": 5, "lng": 6}, "acc": [1, 2, 3, 4]}
            )
        )

        multi_points = points.get_multi_points()
        self.assertEqual(multi_points.centroid.x, 5)
        self.assertEqual(multi_points.centroid.y, 4)

    def test_is_in_place(self):
        points = FramePoints()
        points.append(
            FramePoint.parse(
                {
                    "time": 10,
                    "gps": {"lat": 53.3497913, "lng": -6.2603686},
                    "acc": [1, 2, 3, 4],
                }
            )
        )

        self.assertTrue(points.is_in_place("Dublin, Ireland"))
        self.assertFalse(points.is_in_place("Paris, France"))
        self.assertFalse(points.is_in_place("Blah blah blah"))

    def test_country(self):
        points = FramePoints()
        points.append(
            FramePoint.parse(
                {
                    "time": 10,
                    "gps": {"lat": 53.3497913, "lng": -6.2603686},
                    "acc": [1, 2, 3, 4],
                }
            )
        )
        self.assertEqual(points.country, "IE")

    def test_content_hash(self):
        points = FramePoints()
        points.append(
            FramePoint.parse(
                {"time": 10, "gps": {"lat": 1, "lng": 2}, "acc": [1, 2, 3, 4]}
            )
        )
        points.append(
            FramePoint.parse(
                {"time": 20, "gps": {"lat": 3, "lng": 4}, "acc": [1, 2, 3, 4]}
            )
        )
        points.append(
            FramePoint.parse(
                {"time": 30, "gps": {"lat": 5, "lng": 6}, "acc": [1, 2, 3, 4]}
            )
        )
        self.assertEqual(points.content_hash, "c8765c4a19d013541f9c2d2c9428c178")
