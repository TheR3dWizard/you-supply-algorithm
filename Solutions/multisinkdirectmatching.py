from collections import defaultdict
from typing import List,Optional
from Simulation_Frame import Path,Simulation,Solution,Node
from .DirectMatching import DirectMatching

class MultiSinkDirectMatching(DirectMatching):
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

        for node in nodes:
            if node.is_source:
                source_nodes[node.item].append(node)
                source_items.add(node.item)
            else:
                sink_nodes[node.item].append(node)
                sink_items.add(node.item)


        for item in source_nodes.keys():
            sinks = sink_nodes[item]
            min_sink = min(sinks,key= lambda x: abs(x.value)).value
            sources:List[Node] = source_nodes[item]
            for source in sources:
                path = Path([source])
                amount_left = source.value
                closest_sinks = sorted(sinks,key=lambda x:source.get_distance(x))
                for sink in closest_sinks:
                    if self.simulation.is_node_satisfied(sink):
                        continue
                    val = abs(sink.value)
                    if val <= amount_left:
                        path.add_node(sink)
                        self.simulation.satisfy_node(sink)
                        amount_left -= val

                    if amount_left < min_sink:
                        break
                
                if len(path.nodes) == 1: #No sinks
                    continue
                self.simulation.satisfy_node(source)
                paths.append(path)
        
        self.paths = paths
        return paths

                
        
    
