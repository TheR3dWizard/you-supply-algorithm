from typing import Optional,List
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
    
    def __str__(self):
        return self.__repr__()
    



        



