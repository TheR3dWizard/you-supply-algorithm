import os
import sys

# Ensure project root (containing `Simulation_Frame`) is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Simulation_Frame import Location, Node, Path, PathVisualizer


def build_sample_paths():
    # Simple square path
    p1 = Path(
        nodes=[
            Node("itemA", 10, Location(0, 0)),
            Node("itemA", -5, Location(10, 0)),
            Node("itemA", -5, Location(10, 10)),
        ]
    )

    # Diagonal line path
    p2 = Path(
        nodes=[
            Node("itemB", 8, Location(0, 0)),
            Node("itemB", -4, Location(5, 5)),
            Node("itemB", -4, Location(10, 10)),
            Node("itemB", 0, Location(15, 15)),
        ]
    )

    # Zig-zag path
    p3 = Path(
        nodes=[
            Node("itemC", 6, Location(0, 0)),
            Node("itemC", -3, Location(5, 2)),
            Node("itemC", -3, Location(10, 0)),
            Node("itemC", 0, Location(15, 3)),
        ]
    )

    return [p1, p2, p3]


def main():
    paths = build_sample_paths()
    visualizer = PathVisualizer(paths)
    visualizer.visualize()


if __name__ == "__main__":
    main()


