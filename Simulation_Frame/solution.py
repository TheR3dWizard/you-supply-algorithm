from abc import ABC, abstractmethod
import csv
from typing import List, Optional
from .node import Node
from .path import Path
import matplotlib.pyplot as plt

class Solution(ABC):

    # @abstractmethod
    def set_simulation(self,simulation) -> None:
        self.simulation = simulation

    @abstractmethod
    def solve(self) -> List[Path]:
        pass

    # @abstractmethod
    def get_total_distance(self) -> float:
        tot_dist = 0.0
        for path in self.paths:
            tot_dist += path.get_length()
        self.metrics["total_distance"] = tot_dist
        return tot_dist

    @abstractmethod
    def visualize_paths(self) -> None:
        pass

    @abstractmethod
    def print_paths(self) -> None:
        for i in range(len(self.paths)):
            RED = "\033[0;31m"
            RESET = "\033[0m"
            BOLD = "\033[1m"

            print(f"{RED}{BOLD}{i+1}th path{RESET}\n")
            print(self.paths[i])

    @abstractmethod
    def get_all_metrics(self) -> None:
        pass

    def plotallpaths(self):
        """
        Plots all the different plots into one graph with each path in a different color.
        """
        # plt.figure(figsize=(10, 10))
        colors = plt.colormaps.get_cmap('hsv').resampled(len(self.paths) + 1)
        for i, path in enumerate(self.paths):
            x = [node.location.x for node in path.nodes]
            y = [node.location.y for node in path.nodes]
            plt.plot(x, y, color=colors(i), label=f'Path {i+1}')
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("All Paths")
        # plt.legend()
        plt.show()

    def csv_metrics(self,csv_path:Optional[str]="csv_metrics.csv") -> None:
        with open(csv_path, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.metrics.keys())
            writer.writerow(self.metrics)
