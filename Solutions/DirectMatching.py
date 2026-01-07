from typing import List,Optional
from Simulation_Frame import Path,Simulation,Solution

class DirectMatching(Solution):
    def __init__(self,simulation:Optional[Simulation]):
        self.paths = []
        self.simulation = simulation if simulation else None

    def set_simulation(self, simulation):
        return super().set_simulation(simulation)

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
        return super().get_total_distance()
    
    def get_unsatisfied_nodes(self):
        return self.simulation.get_unsatisfied_nodes()

    def get_satisfaction_metrics(self):
        tot_nodes = self.simulation.size
        unsat_nodes = len(self.get_unsatisfied_nodes())
        satisfaction_percent = ((tot_nodes - unsat_nodes) / tot_nodes) * 100
        print(f"Total Nodes: {tot_nodes}")
        print(f"Unsatisfied Nodes: {unsat_nodes}")
        print(f"Satisfaction Percentage: {satisfaction_percent:.2f}%")
        return satisfaction_percent

    def visualize_paths(self, paths):
        return None
    
    def print_paths(self):
        return super().print_paths()

    def get_all_metrics(self,out:Optional[str]=None):
        tot_dist = self.get_total_distance()
        satisfaction_percent = self.get_satisfaction_metrics()

        if not out:
            print(f"Total Distance of all Paths: {tot_dist}")
            print(f"Satisfaction Percentage: {satisfaction_percent:.2f}%")
        else:
            with open(out,'a') as f:
                f.write("Direct Matching Algorithm Metrics:\n")
                f.write(f"Total Distance of all Paths: {tot_dist}\n")
                f.write(f"Satisfaction Percentage: {satisfaction_percent:.2f}%\n")
        
    
