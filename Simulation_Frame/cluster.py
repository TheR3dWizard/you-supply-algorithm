from collections import defaultdict
from .node import Node
from typing import List,Optional

class Cluster:
    def __init__(self,nodes:Optional[List[Node]]):
        self.nodes = nodes if nodes else []
        self.sinks = [node for node in nodes if not node.is_source]
        self.sources = [node for node in nodes if node.is_source]
        self.size = len(self.nodes)
        self.inventory = defaultdict(int)
    
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

    def remove_sink(self,node:Node):
        if node not in self.sinks:
            raise ValueError("Node not in sinks of cluster.")
        self.size -= 1
        self.nodes.remove(node)
        self.sinks.remove(node)
    
    def remove_source(self,node:Node):
        if node not in self.sources:
            raise ValueError("Node not in sources of cluster.")
        self.size -= 1
        self.nodes.remove(node)
        self.sources.remove(node)

    def get_size(self) -> int:
        return self.size
    
    def updateinventory(self):
        self.inventory = defaultdict(int)
        for node in self.sources:
            self.inventory[node.item] += node.value
        for node in self.sinks:
            self.inventory[node.item] += node.value

    def __repr__(self):
        return (
            f"Cluster(Size: {self.size}, "
            f"Sources: {self.sources}, "
            f"Sinks: {self.sinks})"
        )