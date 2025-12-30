from typing import List
from Simulation import Location,Node,Solution,Path


class DirectMatching(Solution):
    def __init__(self):
        self.paths = []

    def solve(self,nodes:List[Node]) -> List[Path]:
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

            if node.item in items_dict.keys:
                items_dict[node.item].append(node)
            else:
                items_dict[node.item] = [node]

        for item in items_dict.keys:
            available = items_dict[item]
            for source_node in available:
                if source_node.is_source:
                    size = abs(source_node.value)
                    fill_size = 0
                    sink_node = None

                    #select suitable sink node
                    for sink_node_cand in available:
                        if sink_node_cand.is_source:
                            pass
                        if abs(sink_node_cand.value) < size and abs(sink_node_cand.value) > fill_size:
                            fill_size = abs(sink_node_cand.value) 
                            sink_node = sink_node_cand

                    path = Path(nodes=[source_node,sink_node])
                    paths.append(Path)
        
        return paths