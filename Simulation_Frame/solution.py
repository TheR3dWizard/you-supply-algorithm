from abc import ABC, abstractmethod
from typing import List
from .node import Node
from .path import Path

class Solution(ABC):
    @abstractmethod
    def solve(self) -> List[Path]:
        pass

    @abstractmethod
    def get_total_distance(self) -> float:
        pass

    @abstractmethod
    def visualize_paths(self) -> None:
        pass

    @abstractmethod
    def print_paths(self) -> None:
        pass

    @abstractmethod
    def get_all_metrics(self) -> None:
        pass