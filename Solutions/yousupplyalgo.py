from typing import Optional,List
from Simulation_Frame import Solution,Simulation,Node,Path,Cluster
from sklearn.cluster import SpectralClustering


class YouSupplyAlgo(Solution):

    def __init__(self,simulation:Optional[Simulation]):
        self.paths = []
        self.simulation = simulation if simulation else None

    def geographical_cluster(self,nodes:List[Node]) -> List[List[Node]]:
        pass

    def feasibility_cluster(self,nodes:List[Node]) -> List[Node]:
        pass

    def create_path(self,nodes:List[Node]) -> Path:
        pass

    def solve(self):
        paths:List[Path] = []
        nodes = self.simulation.get_nodes()
        geo_clusters = self.geographical_cluster(nodes)

        for geo_cluster in geo_clusters:
            feas_cluster = self.feasibility_cluster(geo_cluster)
            path = self.create_path(feas_cluster)
            paths.append(path)


    
    def get_total_distance(self):
        return super().get_total_distance()
    
    def print_paths(self):
        return super().print_paths()
    
    def visualize_paths(self):
        return super().visualize_paths()
    