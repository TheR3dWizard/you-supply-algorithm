from collections import defaultdict

from Simulation_Frame.node import Node


class Inventory:
    def __init__(self):
        self.inventory = defaultdict(int)
        self.weights = defaultdict(lambda: 1)
        self.weight = 0
    
    def add_node(self,node:Node,weight=None):
        if not node.is_source:
            raise TypeError("Node should be a source, cannot add sink to warehouse")
        self.inventory[node.item] += node.value 
        if not weight:
            weight = self.get_item_weight(node.item)
        amount = node.value*weight
        self.weight += amount

    def add_item(self,item,value,weight=1):
        if item in self.weights.keys():
            weight = self.weights[item]
        else:
            self.weights[item] = weight
        amount = value*weight
        self.weight += amount
        self.inventory[item] += value

    def remove_item(self,item,value):
        if not self.inventory[item] >= value:
            raise ValueError(f"Removing more of {item} than what is present (Tried to remove f{value})")
        self.inventory[item] -= value
        weight = self.weights[item]
        amount = value*weight
        self.weight -= amount

    def get_amount(self,item):
        return self.inventory[item]
    
    def get_item_weight(self,item):
        if item in self.weights.keys():
            return self.weights[item]
        return 1

    def is_empty(self):
        for item in self.get_items():
            if self.get_amount(item) != 0:
                return False
        return True

    def get_weight(self):
        return self.weight
    
    def get_items(self):
        return list(self.inventory.keys())
    
    def is_feasible_sink(self,sink:Node):
        available = self.inventory[sink.item]
        return available >= abs(sink.value)
    
    def __str__(self):
        ret = ""
        for item in self.get_items():
            ret += f"\n{item}:{self.get_amount(item)}"
        
        return ret

        