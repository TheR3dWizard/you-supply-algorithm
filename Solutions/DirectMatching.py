from typing import List,Optional
from Simulation_Frame import Path,Simulation,Solution

class DirectMatching(Solution):
    def __init__(self,simulation:Optional[Simulation]):
        self.paths = []
        self.simulation = simulation if simulation else None

    def solve(self) -> List[Path]:

        
        if self.simulation:
            nodes = self.simulation.get_nodes()
        else:
            print("No simulation present")
            return -1

        source_nodes = []
        source_items = set()

        sink_nodes = []
        sink_items = set()

        items_dict = {}
        paths = []

        for node in nodes:
            if node.is_source:
                source_nodes.append(node)
                source_items.add(node.item)
            else:
                sink_nodes.append(node)
                sink_items.add(node.item)

            if node.item in items_dict.keys():
                items_dict[node.item].append(node)
            else:
                items_dict[node.item] = [node]

        for item in items_dict.keys():
            available = items_dict[item]
            for source_node in available:
                if source_node.is_source:
                    size = abs(source_node.value)
                    fill_size = 0
                    sink_node = None

                    #select suitable sink node
                    for sink_node_cand in available:
                        if sink_node_cand.is_source:
                            continue
                        if self.simulation.is_node_satisfied(sink_node_cand):
                            continue
                        if abs(sink_node_cand.value) < size and abs(sink_node_cand.value) > fill_size:
                            fill_size = abs(sink_node_cand.value) 
                            sink_node = sink_node_cand

                    if not sink_node:
                        continue
                    self.simulation.satisfy_node(source_node)
                    self.simulation.satisfy_node(sink_node)
                    path = Path(nodes=[source_node,sink_node])
                    paths.append(path)
        self.paths = paths
        return paths
    
    def get_total_distance(self):
        tot_dist = 0.0
        for path in self.paths:
            tot_dist += path.get_length()
        return tot_dist
    
    def get_unsatisfied_nodes(self):
        return self.simulation.get_unsatisfied_nodes()

    def visualize_paths(self, paths):
        return None
    
    def print_paths(self):
        for i in range(len(self.paths)):
            RED = "\033[0;31m"
            RESET = "\033[0m"
            BOLD = "\033[1m"

            print(f"{RED}{BOLD}{i+1}th path{RESET}\n")
            print(self.paths[i])

    def get_all_metrics(self):
        return super().get_all_metrics()
    
