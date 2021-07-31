from bike.utils import get_combined_id


EDGE_CACHE = {}


def get_edge_data(graph, origin_uuid, destination_uuid):

    combined_id = get_combined_id(origin_uuid, destination_uuid)

    try:
        return EDGE_CACHE[combined_id]
    except KeyError:
        EDGE_CACHE[combined_id] = graph.get_edge_data(
            origin_uuid,
            destination_uuid
        )
        return EDGE_CACHE[combined_id]
