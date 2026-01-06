from .node import Node
from typing import List,Optional

class Cluster:
    def __init__(self,nodes:Optional[List[Node]]):
        self.nodes = nodes if nodes else []
        self.sinks = [node for node in nodes if not node.is_source]
        self.sources = [node for node in nodes if node.is_source]
        self.size = len(self.nodes)
    
    def add_sink(self,node:Node):
        if node.is_source:
            raise ValueError("Node is a source, cannot add as sink.")
        self.size += 1
        self.nodes.append(node)
        self.sinks.append(node)

    def add_source(self,node:Node):
        if not node.is_source:
            raise ValueError("Node is a sink, cannot add as source.")
        self.size += 1
        self.nodes.append(node)
        self.sources.append(node)

    def get_size(self) -> int:
        return self.size