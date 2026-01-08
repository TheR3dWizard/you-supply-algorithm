from __future__ import annotations

import curses
from typing import List, Sequence, Union

from .node import Node
from .path import Path


PathLike = Union[Path, Sequence[Node]]


class PathVisualizer:
    """
    Terminal-based interactive viewer for paths.

    - Takes a list of paths (each a `Path` instance or a `Sequence[Node]`).
    - Renders one path at a time in a full-screen, vim/nano-like interface.
    - Use LEFT / RIGHT arrow keys to switch between paths.
    - Use 'q' to quit.
    - Nodes are connected sequentially (0->1->2->...), last node is NOT connected to 0.
    """

    def __init__(self, paths: List[PathLike]):
        # Normalize to list of lists of nodes
        normalized_paths: List[List[Node]] = []
        for p in paths:
            if isinstance(p, Path):
                normalized_paths.append(list(p.nodes))
            else:
                # assume it is already a sequence of Node
                normalized_paths.append(list(p))
        self.paths: List[List[Node]] = normalized_paths
        self.current_index: int = 0

    def visualize(self) -> None:
        """
        Entry point: start the curses UI.
        """
        if not self.paths:
            print("No paths to visualize.")
            return
        curses.wrapper(self._main)

    # ---- internal helpers ----

    def _main(self, stdscr) -> None:
        curses.curs_set(0)  # hide cursor
        stdscr.nodelay(False)
        stdscr.keypad(True)

        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()

            self._draw_header(stdscr, max_x)
            self._draw_footer(stdscr, max_y, max_x)
            self._draw_current_path(stdscr, max_y, max_x)

            stdscr.refresh()

            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                break
            elif key == curses.KEY_RIGHT:
                if self.current_index < len(self.paths) - 1:
                    self.current_index += 1
            elif key == curses.KEY_LEFT:
                if self.current_index > 0:
                    self.current_index -= 1

    def _draw_header(self, win, max_x: int) -> None:
        title = " Path Visualizer "
        info = f"[Path {self.current_index + 1}/{len(self.paths)}]"
        header = f"{title}{info}".ljust(max_x)
        try:
            win.addstr(0, 0, header, curses.A_REVERSE)
        except curses.error:
            # Ignore if terminal is too small
            pass

    def _draw_footer(self, win, max_y: int, max_x: int) -> None:
        footer = " ←/→: switch path   q: quit ".ljust(max_x)
        try:
            win.addstr(max_y - 1, 0, footer, curses.A_REVERSE)
        except curses.error:
            pass

    def _draw_current_path(self, win, max_y: int, max_x: int) -> None:
        """
        Draw the currently selected path in the available drawing area.
        """
        nodes = self.paths[self.current_index]
        if not nodes:
            return

        # drawable area (exclude header and footer)
        top = 1
        bottom = max_y - 2
        left = 0
        right = max_x - 1

        height = max(1, bottom - top + 1)
        width = max(1, right - left + 1)

        # Collect coordinates
        xs = [n.location.x for n in nodes]
        ys = [n.location.y for n in nodes]

        min_x, max_x_coord = min(xs), max(xs)
        min_y, max_y_coord = min(ys), max(ys)

        # Avoid division by zero when all nodes share the same coord
        span_x = max(1, max_x_coord - min_x)
        span_y = max(1, max_y_coord - min_y)

        # Scale function: map world coordinates -> terminal coordinates
        def to_screen(node: Node) -> tuple[int, int]:
            norm_x = (node.location.x - min_x) / span_x
            norm_y = (node.location.y - min_y) / span_y

            col = left + int(norm_x * (width - 1))
            # y axis is inverted in terminal (0 at top)
            row = top + int((1.0 - norm_y) * (height - 1))
            return row, col

        # Draw edges between consecutive nodes only (no wrap-around)
        for i in range(len(nodes) - 1):
            n1 = nodes[i]
            n2 = nodes[i + 1]
            r1, c1 = to_screen(n1)
            r2, c2 = to_screen(n2)
            self._draw_line(win, r1, c1, r2, c2)

        # Draw nodes on top of edges
        for idx, node in enumerate(nodes):
            r, c = to_screen(node)
            ch = "S" if node.is_source else "T"
            label = ch
            try:
                win.addch(r, c, label)
            except curses.error:
                # Might be off-screen; ignore
                pass

    def _draw_line(self, win, r1: int, c1: int, r2: int, c2: int) -> None:
        """
        Simple Bresenham line drawing between (r1, c1) and (r2, c2).
        """
        dr = abs(r2 - r1)
        dc = abs(c2 - c1)
        sr = 1 if r1 < r2 else -1
        sc = 1 if c1 < c2 else -1
        err = (dr - dc)

        r, c = r1, c1
        while True:
            try:
                win.addch(r, c, ".")
            except curses.error:
                pass
            if r == r2 and c == c2:
                break
            e2 = 2 * err
            if e2 > -dc:
                err -= dc
                r += sr
            if e2 < dr:
                err += dr
                c += sc


