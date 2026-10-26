"""广度优先搜索（BFS）。

队列（FIFO）保证按层数扩展，在无权图上首次到达终点即最短路。
时间 O(V+E)，空间 O(V)——队列峰值宽度在网格上约为 O(√n)，
这也是它和 DFS 最直观的空间差异。
"""
from __future__ import annotations

from collections import deque

from ..maze import Maze, Cell
from .base import SolveResult, reconstruct, check_endpoints, unreachable


def solve(maze: Maze, start: Cell | None = None, end: Cell | None = None,
          on_event=None) -> SolveResult:
    """on_event(kind, cell) 可选回调：kind ∈ {"visit", "frontier"}，供 GUI 动画。"""
    start, end = check_endpoints(maze, start, end)
    emit = on_event or (lambda kind, cell: None)

    queue = deque([start])
    visited = {start}
    parent: dict[Cell, Cell] = {}
    expanded = 0
    peak = 1

    while queue:
        cur = queue.popleft()
        emit("visit", cur)
        expanded += 1
        if cur == end:
            return SolveResult(reconstruct(parent, start, end), expanded, len(visited), peak)
        for nb in maze.open_neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = cur
                queue.append(nb)
                emit("frontier", nb)
        peak = max(peak, len(queue))

    return unreachable(expanded, len(visited), peak)
