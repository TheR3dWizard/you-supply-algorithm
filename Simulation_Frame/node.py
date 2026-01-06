class Node:
    def __init__(self, item:str,value:int,location):
        self.item = item
        self.value = value
        self.location = location
        self.is_source = value > 0