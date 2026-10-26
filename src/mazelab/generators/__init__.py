"""迷宫生成算法。

三个算法共同的事件协议（供 GUI 动画逐帧消费）：
- ("active", cell)  当前正在处理的格子，动画中高亮
- ("carve", a, b)   刚打通 a—b 之间的墙

所有算法直接在传入的 Maze 上原地拆墙，均为生成器函数，
rand() 一律来自显式传入的 random.Random，保证同一种子结果可复现。
"""
from .backtracker import generate as backtracker_generate
from .prim import generate as prim_generate
from .kruskal import generate as kruskal_generate
from .braid import braid

# name -> {"label": 中文显示名, "func": 生成器函数}
GENERATORS: dict[str, dict] = {
    "backtracker": {"label": "递归回溯", "func": backtracker_generate},
    "prim": {"label": "随机 Prim", "func": prim_generate},
    "kruskal": {"label": "Kruskal", "func": kruskal_generate},
}

__all__ = ["GENERATORS", "braid"]
