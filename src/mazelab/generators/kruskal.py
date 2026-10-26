"""Kruskal 迷宫生成（并查集 + 随机化边序）。

把迷宫看成「全封闭的图」：所有相邻格子对都是候选边，权重随机。
按随机顺序扫描每条边，若两端属于不同连通分量则拆墙合并——正是
Kruskal 最小生成树的流程，随机权重下得到均匀随机生成树。

并查集用「路径减半 + 按秩合并」，单次操作近似 O(α(n))，整体 O(E·α(E))，
E = 2·rows·cols - rows - cols。
"""
from __future__ import annotations

import random

from ..maze import Maze, Cell


class UnionFind:
    """并查集：parent 数组 + 路径减半 + 按秩合并。"""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # 路径减半
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        """合并两个集合；已在同一集合返回 False（该边形成环，跳过）。"""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def generate(maze: Maze, start: Cell | None = None, rng: random.Random | None = None):
    # Kruskal 没有起点概念，start 仅用于与其他生成器签名一致
    rng = rng if rng is not None else random.Random()

    cells = [(r, c) for r in range(maze.rows) for c in range(maze.cols)]
    index = {cell: i for i, cell in enumerate(cells)}

    # 每条内部边只枚举一次：只看每个格子的 E、S 两个方向
    edges: list[tuple[Cell, Cell]] = []
    for cell in cells:
        for d in ("E", "S"):
            nb = maze.neighbor(cell, d)
            if nb is not None:
                edges.append((cell, nb))
    rng.shuffle(edges)

    uf = UnionFind(len(cells))
    for a, b in edges:
        if uf.union(index[a], index[b]):
            maze.carve(a, b)
            yield ("carve", a, b)
