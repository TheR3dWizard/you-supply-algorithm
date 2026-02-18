from typing import List,Optional
from .node import Node
from .location import Location
from .inventory import Inventory
from collections import defaultdict

class Warehouse(Node):
    def __init__(self,nodes:List[Node],location:Location):
        self.nodes:List[Node] = []
        self.inventory = Inventory()
        self.location = location
        self.update_inventory()
        for node in nodes:
            self.add_node(node)
        self.is_source = True

    def add_node(self,node:Node):
        if not node.is_source:
            raise TypeError("Node should be a source, cannot add sink to warehouse")
        self.nodes.append(node)
        self.inventory.add_node(node)
    
    def update_inventory(self):
        for node in self.nodes:
            self.inventory.add_node(node)

    def satisfies_sink(self,sink:Node):
        return self.inventory.is_feasible_sink(sink)

    def remove_item(self,item,value):
        self.inventory.remove_item(item,value)

    def check(self,driver:defaultdict[int]):
        for item in self.inventory.get_items():
            val = self.inventory.get_amount(item)
            available = driver[item]
            if val > 0:
                continue
            if val < 0 and available >= abs(val):
                continue
            return False
        return True
    
    def add_inventory(self,inventory:Inventory):
        for item in inventory.get_items():
            value = inventory.get_amount(item)
            self.inventory.add_item(item,value)

    def is_empty(self):
        return self.inventory.is_empty()

    def __str__(self):
        
        RESET = "\033[0m"
        BOLD = "\033[1m"

        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        MAGENTA = "\033[95m"
        BLUE = "\033[94m"

        source_text = "Yes" if self.is_source else "No"
        source_color = GREEN if self.is_source else YELLOW

        return (
            f"\n{BOLD}WAREHOUSE{RESET}"
            # f"\n{BOLD}{CYAN}Item:{RESET} {[node.item for node in self.nodes]}\n"
            # f"{BOLD}{GREEN}Value:{RESET} {[node.value for node in self.nodes]}\n"
            f"{BOLD}{MAGENTA}Location:{RESET} {self.location}\n"
            f"{BOLD}{BLUE}Source:{RESET} {source_color}{source_text}{RESET}\n"
        )

    def __repr__(self):
        return (
            # f"<Item:{[node.item for node in self.nodes]}, "
            # f"Value:{[node.value for node in self.nodes]}, "
            f"Location:{self.location}, "
            f"Source:{self.is_source}>"
        )






