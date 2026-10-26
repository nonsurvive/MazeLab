"""递归回溯（深度优先）迷宫生成 —— 迭代版。

对应教材的 DFS 生成迷宫思想：从起点出发，随机走向一个未访问邻居并拆墙；
无路可走时回溯。这里用**显式栈**代替递归：101×101 有上万个格子，
Python 默认递归深度约 1000，直接递归会 RecursionError。

时间 O(n)、额外空间 O(n)（栈 + 已访问集合），n 为格子数。
产出的迷宫走廊长、死胡同深，路径弯曲度高。
"""
from __future__ import annotations

import random

from ..maze import Maze, Cell, DIR_ORDER


def generate(maze: Maze, start: Cell | None = None, rng: random.Random | None = None):
    """在 maze 上原地生成完美迷宫，逐步 yield 动画事件。"""
    rng = rng if rng is not None else random.Random()
    start = start if start is not None else maze.start

    stack: list[Cell] = [start]
    visited = {start}
    yield ("active", start)

    while stack:
        cur = stack[-1]
        # 收集当前格子的所有未访问邻居（固定方向顺序，保证同种子可复现）
        options = [
            nb
            for d in DIR_ORDER
            if (nb := maze.neighbor(cur, d)) is not None and nb not in visited
        ]
        if options:
            nxt = rng.choice(options)
            maze.carve(cur, nxt)
            visited.add(nxt)
            stack.append(nxt)
            yield ("carve", cur, nxt)
            yield ("active", nxt)
        else:
            stack.pop()  # 回溯
