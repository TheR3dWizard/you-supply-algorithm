from collections import defaultdict
from .inventory import Inventory
from .node import Node
from .location import Location
from typing import Optional

class Driver:
    def __init__(self,capacity,location:Optional[Location]=None):
        self.capacity = capacity
        self.inventory = Inventory()
        self.location = Location(0,0) if not location else location

    def can_add(self,item,value,weight=1):
        amount = value*weight
        if self.get_remaining_capacity() >= amount:
            return True
        return False
    
    def add_item(self,item,value,weight=1,node:Optional[Node]=None):
        if self.can_add(item,value,weight):
            self.inventory.add_item(item,value,weight)
        if node:
            self.set_location(node.location)
        

    def can_add_node(self,node:Node,weight = 1):
        item,value = node.unpack()
        weight = self.inventory.get_item_weight(item)
        return self.can_add(item,value,weight)

    def add_node(self,node:Node):
        if self.can_add_node(node):
            self.inventory.add_node(node)
        self.set_location(node.location)

    def get_items(self):
        return self.inventory.get_items()

    def remove_item(self,item,value):
        if not self.inventory.get_amount() >= value:
            raise ValueError(f"Removing more of {item} than what is present (Tried to remove f{value})")
        self.inventory.remove_item(item,value) 

    def set_location(self,location:Location):
        self.location = location

    def copy(self):
        return Driver(self.capacity) 
    
    def get_amount(self,item):
        return self.inventory.get_amount(item)
    
    def get_remaining_capacity(self):
        return self.capacity - self.inventory.weight

    def is_full(self):
        return self.inventory.get_weight() == self.capacity

    def __str__(self):
        return f"Driver with an inventory of: {self.inventory}"
        
