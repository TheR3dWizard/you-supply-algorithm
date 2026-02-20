import osmnx as ox
import networkx as nx
from .newprint import NewPrint
newprint = NewPrint("osmrouter")

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
    newprint.newprint(f"Graph initialized with {len(_gu.nodes)} nodes and {len(_gu.edges)} edges",skipconsole=True)

def road_distance(lat1: float, lon1: float, lat2: float, lon2: float,
                  weight: str = "length") -> float:
    """Shortest path distance on the road network between two geo points."""
    if _gu is None:
        raise RuntimeError("Graph not initialized. Call init_graph first.")
    newprint.newprint(f"Calculating road distance between {lat1}, {lon1} and {lat2}, {lon2}",skipconsole=True)
    # osmnx expects X=lon, Y=lat
    orig_node = ox.distance.nearest_nodes(_gu, X=lon1, Y=lat1)
    dest_node = ox.distance.nearest_nodes(_gu, X=lon2, Y=lat2)
    newprint.newprint(f"Nearest nodes: {orig_node}, {dest_node}",skipconsole=True)   
    return nx.shortest_path_length(_gu, orig_node, dest_node, weight=weight)

def get_bounding_box(center_point: tuple[float, float], dist: float = 5000) -> dict:
    """Get bounding box coordinates for a given center point and distance."""
    if _gu is None:
        raise RuntimeError("Graph not initialized. Call init_graph first.")

    longmin, latmin, longmax, latmax = ox.utils_geo.bbox_from_point(center_point, dist=dist)
    newprint.newprint(f"Bounding box: {longmin}, {latmin}, {longmax}, {latmax}")
    return {
        "latitude":[latmin, latmax],
        "longitude":[longmin, longmax]
    }