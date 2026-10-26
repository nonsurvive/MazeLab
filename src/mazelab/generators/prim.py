"""随机 Prim 迷宫生成。

维护一个「前沿」集合（与已生成区域相邻、尚未加入的格子）。每步随机取出
一个前沿格子，再随机选一个已生成邻居作为锚点拆墙并入。前沿用「集合判重 +
列表 swap-pop 随机删除」实现，单步 O(1)~O(4)，整体 O(n)。

与递归回溯相反，Prim 生成的迷宫短岔路多、枝杈茂密，两种纹理对比明显。
"""
from __future__ import annotations

import random

from ..maze import Maze, Cell, DIR_ORDER


def generate(maze: Maze, start: Cell | None = None, rng: random.Random | None = None):
    rng = rng if rng is not None else random.Random()
    start = start if start is not None else maze.start

    in_maze: set[Cell] = {start}
    frontier: list[Cell] = []          # 候选格子，允许与 frontier_set 同步冗余
    frontier_set: set[Cell] = set()
    yield ("active", start)

    def push_frontier(cell: Cell) -> None:
        for d in DIR_ORDER:
            nb = maze.neighbor(cell, d)
            if nb is not None and nb not in in_maze and nb not in frontier_set:
                frontier_set.add(nb)
                frontier.append(nb)

    push_frontier(start)
    while frontier:
        # 等价于从前沿均匀随机取一个：swap-pop，O(1) 删除且不打乱其余元素
        idx = rng.randrange(len(frontier))
        cell = frontier[idx]
        frontier[idx] = frontier[-1]
        frontier.pop()
        frontier_set.discard(cell)

        anchors = [nb for d in DIR_ORDER if (nb := maze.neighbor(cell, d)) is not None and nb in in_maze]
        anchor = rng.choice(anchors)
        maze.carve(cell, anchor)
        in_maze.add(cell)
        yield ("carve", cell, anchor)
        yield ("active", cell)
        push_frontier(cell)
