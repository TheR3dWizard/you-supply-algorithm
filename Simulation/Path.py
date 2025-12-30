from typing import Optional,List
from Node import Node

class Path:
    def __init__(self,nodes:Optional[List[Node]]=None):
        if nodes is None:
            nodes = []
        self.nodes = nodes

    def get_length(self) -> float:
        total_length = 0.0
        for i in range(1,len(self.nodes)):
            total_length += self.nodes[i-1].location.get_distance(self.nodes[i].location)