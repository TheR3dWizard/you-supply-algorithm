from typing import List,Optional
from .node import Node
from .location import Location
from collections import defaultdict

class Warehouse:
    def __init__(self,nodes:List[Node]):
        self.nodes = nodes
        self.inventory = defaultdict(int)

    def compute_center(self,nodes:Optional[List[Node]]) -> Location:
        if not nodes:
            nodes = self.nodes
        x_vals = [node.location.x for node in nodes]
        y_vals = [node.location.y for node in nodes]
        x = sum(x_vals)/len(x_vals)
        y = sum(y_vals)/len(y_vals)
        return Location(x,y)
    
    def update_inventory(self):
        for node in self.nodes:
            self.inventory[node.item] += node.value

    def check(self,driver:defaultdict[int]):
        for item in self.inventory:
            val = self.inventory[item]
            available = driver[item]
            if val > 0:
                continue
            if val < 0 and available >= abs(val):
                continue
            return False
        return True






