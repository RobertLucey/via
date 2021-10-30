from via.base_cache import BaseCaches, BaseCache
from via.constants import BOUNDING_GRAPH_GDFS_NAME


class UtilsBoundingGraphGDFSGraph(BaseCache):

    def __init__(self, *args, **kwargs):
        kwargs['cache_type'] = 'utils_bounding_graph_gdfs_cache'
        super().__init__(*args, **kwargs)


class UtilsBoundingGraphGDFSGraphs(BaseCaches):

    def __init__(self, *args, **kwargs):
        kwargs['child_class'] = UtilsBoundingGraphGDFSGraph
        kwargs['cache_type'] = 'utils_bounding_graph_gdfs_cache'
        super().__init__(*args, **kwargs)

    def get_fn(self, obj):
        xy = list(obj.to_dict().values())[0].xy
        return '%s_%s.pickle' % (
            round(xy[0][0], 2),
            round(xy[1][0], 2)
        )


class BoundingGraphGDFSGraph(BaseCache):

    def __init__(self, *args, **kwargs):
        kwargs['cache_type'] = BOUNDING_GRAPH_GDFS_NAME
        super().__init__(*args, **kwargs)


class BoundingGraphGDFSGraphs(BaseCaches):

    def __init__(self, *args, **kwargs):
        kwargs['child_class'] = BoundingGraphGDFSGraph
        kwargs['cache_type'] = BOUNDING_GRAPH_GDFS_NAME
        super().__init__(*args, **kwargs)

    def get_fn(self, obj):
        return '%s_%s.pickle' % (
            round(min(obj[0].geometry.x), 2),
            round(min(obj[0].geometry.y), 2)
        )


bounding_graph_gdfs_cache = BoundingGraphGDFSGraphs()
bounding_graph_gdfs_cache.load()

utils_bounding_graph_gdfs_cache = UtilsBoundingGraphGDFSGraphs()
utils_bounding_graph_gdfs_cache.load()
