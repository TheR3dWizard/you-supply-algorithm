from collections import defaultdict
from typing import List,Optional
from Simulation_Frame import Path,Simulation,Solution
from .DirectMatching import DirectMatching

class OptimizedDirectMatching(DirectMatching):
    def solve(self) -> List[Path]:

        if self.simulation:
            nodes = self.simulation.get_nodes()
        else:
            print("No simulation present")
            return -1

        source_nodes = defaultdict(list)
        source_items = set()

        sink_nodes = defaultdict(list)
        sink_items = set()

        paths = []
        visited = set()

        for node in nodes:
            if node.is_source:
                source_nodes[node.item].append(node)
                source_items.add(node.item)
            else:
                sink_nodes[node.item].append(node)
                sink_items.add(node.item)

        # function to get the closest node
        closest = lambda node, possibilities: min(
            [(node.get_distance(_), _) for _ in possibilities if _ not in visited],
            key=lambda x: x[0],
        )

        for item in source_nodes.keys():
            available = sink_nodes[item]
            for source_node in source_nodes[item]:
                size = source_node.value
                fill_size = 0
                sink_node = None
                possibilities = set()
                #select suitable sink node
                for sink_node_cand in available:
                    if abs(sink_node_cand.value) < size:
                        possibilities.add(sink_node_cand)
                if len(possibilities) == 0 or len(possibilities-visited) == 0:
                    continue
                _,sink_node = closest(source_node,possibilities)
                visited.add(sink_node)

                self.simulation.satisfy_node(source_node)
                self.simulation.satisfy_node(sink_node)
                path = Path(nodes=[source_node,sink_node])
                paths.append(path)
        self.paths = paths
        return paths

        
    
