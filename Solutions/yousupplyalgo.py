from collections import defaultdict
from typing import Optional,List
from Simulation_Frame import Solution,Simulation,Node,Path,Cluster
from sklearn.cluster import SpectralClustering


class YouSupplyAlgo(Solution):

    def __init__(self,simulation:Optional[Simulation]):
        self.paths = []
        self.simulation = simulation if simulation else None


    def geographical_cluster(self,nodes:List[Node],num_points:int = 50) -> List[Cluster]:

        cluster_list:List[Cluster] = []

        spc = SpectralClustering(
            n_clusters=self.simulation.size // num_points if self.simulation.size // num_points != 0 else 1,
            random_state=42,
            affinity="nearest_neighbors",
        )

        positions = []
        for node in nodes:
            positions.append(node.location.to_tuple())

        spc.fit(positions)
        cluster_labels = spc.labels_
        clusters = defaultdict(list)

        for i, label in enumerate(cluster_labels):
            clusters[label].append(self.simulation.get_nodes()[i])

        print()
        for cluster_nodes in clusters.values():
            cluster = Cluster(nodes=[])
            for node in cluster_nodes:
                if not node.is_source:
                    cluster.add_sink(node)
                else:
                    cluster.add_source(node)
            cluster_list.append(cluster)

        return cluster_list

    def feasibility_cluster(self,cluster:Cluster) -> Cluster:
        pass

    def create_paths(self,cluster:Cluster) -> Path:
        pass

    def solve(self):
        paths:List[Path] = []
        nodes = self.simulation.get_nodes()
        geo_clusters = self.geographical_cluster(nodes)

        for geo_cluster in geo_clusters:
            feas_cluster = self.feasibility_cluster(geo_cluster)
            path = self.create_paths(feas_cluster)
            paths.append(path)


    def get_all_metrics(self):
        return super().get_all_metrics()

    def get_total_distance(self):
        return super().get_total_distance()
    
    def print_paths(self):
        return super().print_paths()
    
    def visualize_paths(self):
        return super().visualize_paths()
    