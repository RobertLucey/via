from via.base_cache import BaseCaches, BaseCache
from via.constants import BOUNDING_GRAPH_GDFS_NAME


class BoundingGraphGDFSGraph(BaseCache):

    def __init__(self, *args, **kwargs):
        kwargs['cache_type'] = BOUNDING_GRAPH_GDFS_NAME
        super().__init__(*args, **kwargs)


class BoundingGraphGDFSGraphs(BaseCaches):

    def __init__(self, *args, **kwargs):
        kwargs['child_class'] = BoundingGraphGDFSGraph
        kwargs['cache_type'] = BOUNDING_GRAPH_GDFS_NAME
        super().__init__(*args, **kwargs)


bounding_graph_gdfs_cache = BoundingGraphGDFSGraphs()
bounding_graph_gdfs_cache.load()
