from typing import List,Optional
import random
import Node,Location

class Simulation:
    def __init__(self,area:int,size:int,range:int,items:List[str]=None):
        self.nodes = []
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

    def get_nodes(self):
        return self.nodes
    
    def __str__(self):
        return f"Number of nodes: {self.size}"

        

sim = Simulation(1000,50,10)
print(sim)

