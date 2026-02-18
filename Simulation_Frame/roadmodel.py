from abc import ABC, abstractmethod

class RoadModel(ABC):
    @abstractmethod
    def predict_time(self, edge:RoadEdge) -> float:
        pass

    @abstractmethod
    def on_traversal(self, edge:RoadEdge, T_obs:float):
        pass

    @abstractmethod
    def expected_cost(self, edge:RoadEdge) -> float:
        pass
