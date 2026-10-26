"""贪心最佳优先搜索（Greedy Best-First）。

只按 h(n)（到终点的曼哈顿距离）排序，完全不看已走代价 g。
速度通常介于 A* 与 BFS 之间，但**不保证最短**——在有环迷宫中
会被启发值「引诱」进局部看似更近的岔路。放入对比实验，
恰好展示了「有信息搜索」中 g 与 h 各自的作用。
"""
from __future__ import annotations

import heapq
from itertools import count

from ..maze import Maze, Cell
from .base import SolveResult, reconstruct, check_endpoints, manhattan, unreachable


def solve(maze: Maze, start: Cell | None = None, end: Cell | None = None,
          on_event=None) -> SolveResult:
    start, end = check_endpoints(maze, start, end)
    emit = on_event or (lambda kind, cell: None)
    tick = count()

    parent: dict[Cell, Cell] = {}
    open_heap = [(manhattan(start, end), next(tick), start)]
    open_set = {start}
    closed: set[Cell] = set()
    expanded = 0
    peak = 1

    while open_heap:
        _, _, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        open_set.discard(cur)
        emit("visit", cur)
        expanded += 1
        if cur == end:
            return SolveResult(reconstruct(parent, start, end), expanded,
                               len(closed) + len(open_set), peak)
        for nb in maze.open_neighbors(cur):
            if nb not in closed and nb not in open_set:
                parent[nb] = cur
                heapq.heappush(open_heap, (manhattan(nb, end), next(tick), nb))
                open_set.add(nb)
                emit("frontier", nb)
        peak = max(peak, len(open_set))

    return unreachable(expanded, len(closed) + len(open_set), peak)
