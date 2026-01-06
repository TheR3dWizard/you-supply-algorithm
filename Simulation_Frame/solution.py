from abc import ABC, abstractmethod,property
from typing import List
from Node import Node
from Path import Path

class Solution(ABC):
    @abstractmethod
    def solve(self,nodes:List[Node]) -> List[Path]:
        pass

    @abstractmethod
    def get_total_distance(self,paths:List[Path]) -> float:
        pass

    @abstractmethod
    def visualize_paths(self,paths:List[Path]) -> None:
        pass