from typing import List,Optional
import random
from .node import Node
from .location import Location
import matplotlib.pyplot as plt
import numpy as np
from .constants import Constants
class Simulation:
    def __init__(self,area:int,size:int,range:int,items:List[str]=None,latmin:np.float64=Constants.DEFAULT_LATMIN,latmax:np.float64=Constants.DEFAULT_LATMAX,longmin:np.float64=Constants.DEFAULT_LONGMIN,longmax:np.float64=Constants.DEFAULT_LONGMAX):
        self.nodes:List[Node] = []
        self.satisfied_nodes = []
        self.area = area
        self.size = size
        self.latmin = latmin
        self.latmax = latmax
        self.longmin = longmin
        self.longmax = longmax
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
            while value == 0:
                value = random.randint(-1*self.range,self.range)
            x_val = np.random.uniform(self.latmin,self.latmax)
            y_val = np.random.uniform(self.longmin,self.longmax)
            location = Location(x_val,y_val)
            node = Node(item,value,location)
            self.nodes.append(node)
            self.satisfied_nodes.append(False)
            # carriage print as a status check for the loop
            print(f"Populated {i+1} nodes",end="\r")
        print(f"Populated {self.size} nodes")

    def add_node(self,node:Node):
        self.nodes.append(node)
        self.satisfied_nodes.append(False)
        self.size += 1

    def load_nodes(self,nodes:Node):
        self.nodes = nodes
        self.satisfied_nodes = [False for _ in nodes]
        self.size = len(nodes)

    def satisfy_node(self,node:Node) -> None:
        i = self.nodes.index(node)
        self.satisfied_nodes[i] = True

    def satisfy_node_index(self,index:int) -> None:
        self.satisfied_nodes[index] = True

    def unsatisfy_node(self,node:Node) -> None:
        i = self.nodes.index(node)
        self.satisfied_nodes[i] = False
    
    def unsatisfy_node_index(self,index:int) -> None:
        self.satisfied_nodes[index] = False

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
    
    def plotnodes(self):
        x = [node.location.x for node in self.nodes]
        y = [node.location.y for node in self.nodes]
        plt.scatter(x, y)
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("Nodes in Simulation")
        plt.show()

    def all_nodes_satisfied(self,sources=False,sinks=False):
        if sources:
            sources = list(filter(lambda x: x.is_source,self.nodes))
            for source in sources:
                if not self.is_node_satisfied(source):
                    return False
        if sinks:
            sinks = list(filter(lambda x: not x.is_source,self.nodes))
            for sink in sinks:
                if not self.is_node_satisfied(sink):
                    return False
        return True



    def __repr__(self):
        size = len(self.nodes)
        ret = ""
        ret += f"Number of nodes: {size}\n"
        for i in range(10 if size > 10 else size):
            ret += f"{i+1}:{self.nodes[i]}"
        
        return ret

    def __str__(self):
        return self.__repr__()

        



