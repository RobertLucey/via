from bike.utils import get_combined_id


EDGE_CACHE = {}


def get_edge_data(graph, origin_uuid: str, destination_uuid: str):
    """

    :param origin_uuid: osmid of the origin node
    :param destination_uuid: osmid of the destination node
    :return: TODO: can't remember exactly what gets returned
    """

    combined_id = get_combined_id(origin_uuid, destination_uuid)

    try:
        return EDGE_CACHE[combined_id]
    except KeyError:
        EDGE_CACHE[combined_id] = graph.get_edge_data(
            origin_uuid,
            destination_uuid
        )
        return EDGE_CACHE[combined_id]
