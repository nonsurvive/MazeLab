"""A* 搜索（曼哈顿启发式）。

f(n) = g(n) + h(n)：已走代价 + 到终点的估计代价。
曼哈顿距离在四邻域网格上可采纳且一致（每步真实代价 1，h 至多降低 1），
配合二叉堆按 f 取最小，首次弹出终点即得最短路。

实现要点：
- 惰性删除：允许同一格子因更优 g 值重复入堆，弹出时用 closed 集合跳过过期项；
- 计数器作为堆元组第二关键字，避免比较 Cell、保证同种子结果确定；
- frontier_peak 统计的是「未关闭的不同节点数」，与 BFS/DFS 口径一致。
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
    tick = count()  # 稳定平局打破：f 相同按插入顺序出堆

    g = {start: 0}
    parent: dict[Cell, Cell] = {}
    open_heap = [(manhattan(start, end), next(tick), start)]
    open_set = {start}      # 堆中未弹出处理的格子（去重口径）
    closed: set[Cell] = set()
    expanded = 0
    peak = 1

    while open_heap:
        _, _, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue  # 过期堆项（已有更优路径处理过）
        closed.add(cur)
        open_set.discard(cur)
        emit("visit", cur)
        expanded += 1
        if cur == end:
            return SolveResult(reconstruct(parent, start, end), expanded,
                               len(closed) + len(open_set), peak)
        for nb in maze.open_neighbors(cur):
            ng = g[cur] + 1
            if nb not in g or ng < g[nb]:
                g[nb] = ng
                parent[nb] = cur
                heapq.heappush(open_heap, (ng + manhattan(nb, end), next(tick), nb))
                open_set.add(nb)
                emit("frontier", nb)
        peak = max(peak, len(open_set))

    return unreachable(expanded, len(closed) + len(open_set), peak)
