import osmnx as ox
import networkx as nx

# Global graph
_gu = None

def init_graph(center_point: tuple[float, float], dist: float = 5000) -> None:
    """
    center_point: (lat, lon)
    dist: radius in meters
    """
    global _gu
    G_directed = ox.graph_from_point(center_point, dist=dist, network_type="drive")
    _gu = ox.convert.to_undirected(G_directed)

def road_distance(lat1: float, lon1: float, lat2: float, lon2: float,
                  weight: str = "length") -> float:
    """Shortest path distance on the road network between two geo points."""
    if _gu is None:
        raise RuntimeError("Graph not initialized. Call init_graph first.")

    # osmnx expects X=lon, Y=lat
    orig_node = ox.distance.nearest_nodes(_gu, X=lon1, Y=lat1)
    dest_node = ox.distance.nearest_nodes(_gu, X=lon2, Y=lat2)

    return nx.shortest_path_length(_gu, orig_node, dest_node, weight=weight)

def get_bounding_box(center_point: tuple[float, float], dist: float = 5000) -> dict:
    """Get bounding box coordinates for a given center point and distance."""
    if _gu is None:
        raise RuntimeError("Graph not initialized. Call init_graph first.")

    longmin, latmin, longmax, latmax = ox.bbox_from_point(center_point, dist=dist)
    return {
        "latitude":[latmin, latmax],
        "longitude":[longmin, longmax]
    }