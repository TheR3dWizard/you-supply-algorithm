from collections import defaultdict
from typing import Optional,List
from Simulation_Frame import Solution,Simulation,Node,Path,Cluster
from sklearn.cluster import SpectralClustering


class YouSupplyAlgo(Solution):

    def __init__(self,simulation:Optional[Simulation],geo_size:int=50):
        self.paths = []
        self.simulation = simulation if simulation else None
        self.geo_size = geo_size


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
        if cluster.sinks == [] or cluster.sources == []:
            print("No sources/sinks in cluster, returning empty cluster")
            return Cluster(nodes=[])
        
        cluster.updateinventory()
        deficits = []
        excesses = []
        for item in cluster.inventory:
            if cluster.inventory[item] < 0:
                # TYPE: (QUANTITY, [NODES])
                deficits.append(
                    [cluster.inventory[item], [_ for _ in cluster.sinks if _.item == item]]
                )
            elif cluster.inventory[item] > 0:
                excesses.append(
                    [
                        cluster.inventory[item],
                        [_ for _ in cluster.sources if _.item == item],
                    ]
                )
        
        for deficit, nodes in deficits:
            while deficit < 0:
                node = min(nodes, key=lambda x: x.value)
                deficit -= node.value
                nodes.remove(node)
                cluster.remove_sink(node)

        if cluster.sinks == []:
            print("No sinks left in cluster, returning empty cluster")
            return Cluster(nodes=[])



        for excess, nodes in excesses:
            while excess > 0:
                node = max(nodes, key=lambda x: x.value)
                if excess - node.value >= 0: #excess cannot go below 0
                    excess -= node.value
                    nodes.remove(node)
                    cluster.remove_source(node)
                else:
                    break
        # TODO: write functionality to change a half excess node into a full excess and fitting node
        # if deficit is -3, and sink is -5, then sink should be converted to a -2 node and freepool should have a -3 node

        if cluster.sources == []:
            print("No sources left in cluster, returning empty cluster")
            return Cluster(nodes=[])

        cluster.updateinventory()
        return cluster


    def create_paths(self,cluster:Cluster) -> List[Path]:
        distance = 0
        visited = set()
        available = defaultdict(int)
        path = []
        subpaths = []
        # if cluster.sinks == [] or cluster.sources == []:
        #     return path

        # function to get the closest node
        closest = lambda node, possibilities: min(
            [(node.get_distance(_), _) for _ in possibilities if _ not in visited],
            key=lambda x: x[0],
        )

        # TODO: make the first node the closest source node to the curpos
        current = cluster.sources[0]
        visited.add(current)
        path.append(current)

        # function to check if a node can be satisfied
        def check(node: Node):
            if node.item in available:
                if available[node.item] >= abs(node.value):
                    return True
                else:
                    return False
            return False

        previndex = 0

        def createsubpath():
            nonlocal previndex  # Add nonlocal keyword to access outer scope variables
            for i in available:
                if available[i] != 0:
                    return
            print("Creating subpath upto index", len(path))
            subpaths.append(Path(path[previndex:]))
            # self.subpaths[-1].plotpath()
            previndex = len(path)

        while len(visited) < cluster.size:
            available[current.item] += current.value
            createsubpath()
            possiblesinks = [
                node for node in cluster.sinks if node not in visited and check(node)
            ]
            if not possiblesinks:
                possiblesources = [
                    node for node in cluster.sources if node not in visited
                ]
                nextdistance, next = closest(current, possiblesources)
            else:
                nextdistance, next = closest(current, possiblesinks)
            distance += nextdistance
            visited.add(next)
            path.append(next)
            current = next

        return subpaths
    
    def solve(self):
        paths:List[Path] = []
        nodes = self.simulation.get_nodes()
        geo_clusters = self.geographical_cluster(nodes,num_points=self.geo_size)

        for geo_cluster in geo_clusters:
            feas_cluster = self.feasibility_cluster(geo_cluster)
            # print(feas_cluster)
            if feas_cluster.size == 0:
                continue
            paths = self.create_paths(feas_cluster)
            self.paths.extend(paths)


    def get_all_metrics(self):
        return super().get_all_metrics()

    def get_total_distance(self):
        tot_dist = 0.0
        for path in self.paths:
            tot_dist += path.get_length()
        return tot_dist
    
    def print_paths(self):
        return super().print_paths()
    
    def visualize_paths(self):
        return super().visualize_paths()
    