from via.models.collisions.collision import Collisions


def get_collisions():
    return Collisions.load_all()
