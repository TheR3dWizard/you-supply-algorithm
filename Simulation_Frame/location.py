class Location:
    def __init__(self, x:int,y:int):
        self.x = x
        self.y = y

    def get_distance(self,other) -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
    
    def __repr__(self):
        return f"({self.x},{self.y})"
    
    def __str__(self):
        return self.__repr__()