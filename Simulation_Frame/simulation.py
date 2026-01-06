from typing import List,Optional
import random
from .node import Node
from .location import Location

class Simulation:
    def __init__(self,area:int,size:int,range:int,items:List[str]=None):
        self.nodes = []
        self.satisfied_nodes = []
        self.area = area
        self.size = size
        if not items:
            self.items = [
                "water bottle",
                "rice",
                "food"
            ]
        else:
            self.items = items
        self.range = range if range else 10

    def populate_nodes(self):
        for i in range(self.size):
            item = random.choice(self.items)
            value = random.randint(-1*self.range,self.range)
            x_val = random.randint(0,self.area)
            y_val = random.randint(0,self.area)
            location = Location(x_val,y_val)
            node = Node(item,value,location)
            self.nodes.append(node)
            self.satisfied_nodes.append(False)

    def satisfy_node(self,node:Node) -> None:
        i = self.nodes.index(node)
        self.satisfied_nodes[i] = True

    def get_unsatisfied_nodes(self) -> List[Node]:
        unsat_nodes = []
        for i in range(len(self.nodes)):
            if self.satisfied_nodes[i] == False:
                unsat_nodes.append(self.nodes[i])
        
        return unsat_nodes
                
    def is_node_satisfied(self,node):
        return node not in self.get_unsatisfied_nodes()

    def get_nodes(self) -> List[Node]:
        return self.nodes
    
    def __repr__(self):
        size = len(self.nodes)
        ret = ""
        ret += f"Number of nodes: {size}\n"
        for i in range(10 if size > 10 else size):
            ret += f"{i+1}:{self.nodes[i]}"
        
        return ret

    def __str__(self):
        return self.__repr__()

        



