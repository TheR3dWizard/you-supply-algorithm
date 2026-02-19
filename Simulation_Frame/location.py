import Simulation_Frame.OSMRouter as OSMRouter

class Location:
    def __init__(self, x:int,y:int):
        self.x = x
        self.y = y

    def get_distance(self,other,euclidean=False,heuristic=None) -> float:
        if euclidean:
            return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
        else:
            return OSMRouter.road_distance(lat1=self.y,
            lon1=self.x,
            lat2=other.y,
            lon2=other.x,
            weight=heuristic if heuristic else "length")
    
    def to_tuple(self) -> tuple:
        return (self.x,self.y)

    def __repr__(self):
        return f"({self.x},{self.y})"
    
    def copy(self):
        return Location(self.x,self.y)

    def __str__(self):
        return self.__repr__()