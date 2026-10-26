"""深度优先搜索（DFS）—— 迭代版，用显式栈代替递归。

栈（LIFO）让搜索一条路走到黑。在树形迷宫（完美迷宫）中任意两点路径
唯一，DFS 找到的就是这条唯一路径；但在有环图中它既不保证最短也不保证
访问顺序有序，只能保证「找到一条路」。

访问标记在「入栈时」完成而非出栈时，保证同一格子至多入栈一次，
栈深受路径长度约束（网格上最坏 O(n)，实际通常远小于 BFS 队列宽度）。
"""
from __future__ import annotations

from ..maze import Maze, Cell
from .base import SolveResult, reconstruct, check_endpoints, unreachable


def solve(maze: Maze, start: Cell | None = None, end: Cell | None = None,
          on_event=None) -> SolveResult:
    start, end = check_endpoints(maze, start, end)
    emit = on_event or (lambda kind, cell: None)

    stack: list[Cell] = [start]
    visited = {start}
    parent: dict[Cell, Cell] = {}
    expanded = 0
    peak = 1

    while stack:
        cur = stack.pop()
        emit("visit", cur)
        expanded += 1
        if cur == end:
            return SolveResult(reconstruct(parent, start, end), expanded, len(visited), peak)
        for nb in maze.open_neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = cur
                stack.append(nb)
                emit("frontier", nb)
        peak = max(peak, len(stack))

    return unreachable(expanded, len(visited), peak)
