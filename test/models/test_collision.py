from unittest import TestCase, skip

from via.models.collisions.collision import (
    Collision,
    Collisions
)


class CollisionTest(TestCase):

    TEST_COLLISION_DATA = {
        'lat': 52.44920547929465,
        'lng': -8.419577187763258,
        'year': 2008,
        'weekday': 'tuesday',
        'gender': 'female',
        'age': 70,
        'vehicle_type': 'car',
        'vehicle': '4',
        'hour': '23-3',
        'circumstances': 'single_vehicle_only',
        'num_fatal': 0,
        'num_minor': 4,
        'num_notinjured': 1,
        'num_serious': 0,
        'num_unknown': 7,
        'speed_limit': 80,
        'severity': 'minor',
        'county': 'limerick',
        'carrf': 0,
        'carri': 0,
        'class2': 88,
        'goodsrf': 0,
        'goodsri': 0,
        'mcycrf': 0,
        'mcycri': 0,
        'otherrf': 0,
        'otherri': 0,
        'pcycrf': 0,
        'pcycri': 0,
        'pedrf': 0,
        'pedri': 0,
        'psvrf': 0,
        'psvri': 0,
        'unknrf': 0,
        'unknri': 0
    }

    def test_gps(self):
        collision = Collision(
            **self.TEST_COLLISION_DATA
        )

        self.assertEquals(
            collision.gps.serialize(),
            {
                'elevation': None,
                'lat': 52.44920547929465,
                'lng': -8.419577187763258
            }
        )

    def test_is_in_place(self):
        collision = Collision(
            **self.TEST_COLLISION_DATA
        )

        self.assertTrue(
            collision.is_in_place(
                {
                    'north': 100,
                    'south': 0,
                    'east': 10,
                    'west': -10
                }
            )
        )

        self.assertFalse(
            collision.is_in_place(
                {
                    'north': 10,
                    'south': -10,
                    'east': -10,
                    'west': 10
                }
            )
        )

    def test_parse(self):
        collision = Collision(
            **self.TEST_COLLISION_DATA
        )
        self.assertEqual(
            Collision.parse(collision),
            collision
        )
        self.assertEqual(
            Collision.parse(self.TEST_COLLISION_DATA).serialize(),
            collision.serialize()
        )


class CollisionsTest(TestCase):

    TEST_COLLISION_DATA = {
        'lat': 52.44920547929465,
        'lng': -8.419577187763258,
        'year': 2008,
        'weekday': 'tuesday',
        'gender': 'female',
        'age': 70,
        'vehicle_type': 'car',
        'vehicle': '4',
        'hour': '23-3',
        'circumstances': 'single_vehicle_only',
        'num_fatal': 0,
        'num_minor': 4,
        'num_notinjured': 1,
        'num_serious': 0,
        'num_unknown': 7,
        'speed_limit': 80,
        'severity': 'minor',
        'county': 'limerick',
        'carrf': 0,
        'carri': 0,
        'class2': 88,
        'goodsrf': 0,
        'goodsri': 0,
        'mcycrf': 0,
        'mcycri': 0,
        'otherrf': 0,
        'otherri': 0,
        'pcycrf': 0,
        'pcycri': 0,
        'pedrf': 0,
        'pedri': 0,
        'psvrf': 0,
        'psvri': 0,
        'unknrf': 0,
        'unknri': 0
    }

    def test_danger(self):
        collisions = Collisions()
        collisions.append(
            Collision(
                **self.TEST_COLLISION_DATA
            )
        )
        collisions.append(
            Collision(
                **self.TEST_COLLISION_DATA
            )
        )

        self.assertEqual(collisions.danger, 2)

    def test_set_filters(self):
        collisions = Collisions()
        self.assertEqual(collisions.filters, {})
        collisions.set_filters({'country': 'ireland'})
        self.assertEqual(collisions.filters, {'country': 'ireland'})

    @skip('todo')
    def test_danger_by_vehicle_type(self):
        pass

    @skip('todo')
    def test_most_northern(self):
        pass

    @skip('todo')
    def test_most_southern(self):
        pass

    @skip('todo')
    def test_most_eastern(self):
        pass

    @skip('todo')
    def test_most_western(self):
        pass

    @skip('todo')
    def test_bbox(self):
        pass

    @skip('todo')
    def test_lat_span(self):
        pass

    @skip('todo')
    def test_lng_span(self):
        pass
