"""braid：向完美迷宫中添加环路。

完美迷宫是生成树，任意两点路径唯一，此时 DFS 也必然走最短路，
求解算法之间的差异只体现在「探索了多少格子」。加入环路后，
最短路与普通 DFS 才会真正分道扬镳——这是对比实验有意义的前提。

做法：找出所有死胡同（度为 1 的格子），以概率 p 为其随机拆掉一面
内部墙。拆墙只增边不删边，图从树变成有环图。
"""
from __future__ import annotations

import random

from ..maze import Maze, DIR_ORDER


def braid(maze: Maze, p: float, rng: random.Random | None = None):
    """以概率 p 消除死胡同，yield ("carve", a, b) 事件。p=1 时消除全部死胡同。"""
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"环路比例 p 应在 [0,1]，收到 {p}")
    rng = rng if rng is not None else random.Random()

    for cell in maze.dead_ends():
        if rng.random() > p:
            continue
        candidates = [
            (d, nb)
            for d in DIR_ORDER
            if (nb := maze.neighbor(cell, d)) is not None and d in maze.walls[cell]
        ]
        if not candidates:  # 例如 1x1 迷宫，四周都是边界，无从拆起
            continue
        d, nb = rng.choice(candidates)
        maze.carve(cell, nb)
        yield ("carve", cell, nb)
