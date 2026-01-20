import pprint
from typing import Optional,List
import matplotlib.pyplot as plt
from .node import Node

class Path:
    def __init__(self,nodes:Optional[List[Node]]=None):
        self.nodes = nodes if nodes else []

    def get_length(self) -> float:

        if self.nodes == []:
            return 0.0

        total_length = 0.0
        for i in range(1,len(self.nodes)):
            total_length += self.nodes[i-1].location.get_distance(self.nodes[i].location)

        return total_length

    def __repr__(self):
        UNDERLINE = "\033[4m"
        RESET = "\033[0m"

        size = len(self.nodes)

        ret = ""
        ret += f"Number of nodes: {size}\n"
        for i in range(size):
            ret += f"{UNDERLINE}{i+1}th Node{RESET}: {self.nodes[i]}\n"
        
        ret += f"{UNDERLINE}{self.get_length()}{RESET}\n"
        return ret
    
    def plotpath(self,color:Optional[str]=None):
        pprint.pprint(self.nodes)
        x = [node.location.x for node in self.nodes]
        y = [node.location.y for node in self.nodes]
        start_node = self.nodes[0]
        end_node = self.nodes[-1]
        color = color if color else "-o"
        plt.plot(x, y, color)
        plt.plot(start_node.location.x, start_node.location.y, "go", label="Start Node")
        plt.plot(end_node.location.x, end_node.location.y, "ro", label="End Node")
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("Path")
        plt.legend()
        print(f"Number of nodes in path: {len(self.nodes)}")
        print(f"Total length of path: {self.get_length()}")
        plt.show()

    def __str__(self):
        return self.__repr__()
    



        



