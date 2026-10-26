"""迷宫的数据模型。

采用「格子 + 墙」表示：rows × cols 个格子，每个格子记录四面墙是否存在。
相邻两个格子共享同一堵墙，因此拆墙/筑墙必须同步更新两侧，这一点由
carve/add_wall 统一保证，外部代码无法制造出不一致的状态。

墙的数据结构为 dict[Cell, set[str]]：哈希表 + 小集合，
neighbors/has_wall 均为 O(1)。
"""
from __future__ import annotations

from collections import deque

Cell = tuple[int, int]  # (row, col)，行号从上往下、列号从左往右，均从 0 开始

# 方向名 -> (行增量, 列增量)。固定顺序保证遍历结果可复现。
DIRS: dict[str, Cell] = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}
DIR_ORDER = ("N", "S", "E", "W")


class Maze:
    """格子迷宫。初始为全封闭（所有墙都在），由生成算法逐步拆墙。"""

    def __init__(self, rows: int, cols: int, start: Cell | None = None, end: Cell | None = None):
        if rows < 1 or cols < 1:
            raise ValueError(f"迷宫尺寸必须 >= 1，收到 rows={rows}, cols={cols}")
        self.rows = rows
        self.cols = cols
        self.start: Cell = start if start is not None else (0, 0)
        self.end: Cell = end if end is not None else (rows - 1, cols - 1)
        if not (self.in_bounds(self.start) and self.in_bounds(self.end)):
            raise ValueError("起点/终点越界")
        self.walls: dict[Cell, set[str]] = {
            (r, c): {"N", "S", "E", "W"} for r in range(rows) for c in range(cols)
        }
        self._edges = 0  # 已打通的相邻格子对数（即图中的边数）

    # ---------- 基本查询 ----------

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _check(self, cell: Cell) -> None:
        if not self.in_bounds(cell):
            raise ValueError(f"格子 {cell} 越界（迷宫为 {self.rows}x{self.cols}）")

    def neighbor(self, cell: Cell, direction: str) -> Cell | None:
        """返回某方向的相邻格子；越界返回 None。"""
        self._check(cell)
        dr, dc = DIRS[direction]
        nb = (cell[0] + dr, cell[1] + dc)
        return nb if self.in_bounds(nb) else None

    def has_wall(self, a: Cell, b: Cell) -> bool:
        """判断相邻格子 a、b 之间是否有墙。墙的信息两侧各存一份，必须一致。"""
        d = self._adjacent_direction(a, b)
        return d in self.walls[a]

    def open_neighbors(self, cell: Cell) -> list[Cell]:
        """返回所有「没有墙隔开」的相邻格子，顺序固定（N,S,E,W），保证可复现。"""
        result = []
        for d in DIR_ORDER:
            nb = self.neighbor(cell, d)
            if nb is not None and d not in self.walls[cell]:
                result.append(nb)
        return result

    def edges(self) -> int:
        """已打通的边数。"""
        return self._edges

    def degree(self, cell: Cell) -> int:
        return len(self.open_neighbors(cell))

    def dead_ends(self) -> list[Cell]:
        """度为 1 的格子（三面墙、只出不进的死胡同）。"""
        return [cell for cell in self.walls if self.degree(cell) == 1]

    # ---------- 修改操作 ----------

    def carve(self, a: Cell, b: Cell) -> None:
        """打通 a、b 之间的墙（两侧同步删除）。要求两格相邻且当前确实有墙。"""
        d = self._adjacent_direction(a, b)
        if d not in self.walls[a]:
            raise ValueError(f"{a} 与 {b} 之间没有墙，不能重复打通")
        self.walls[a].discard(d)
        self.walls[b].discard(OPPOSITE[d])
        self._edges += 1

    def add_wall(self, a: Cell, b: Cell) -> None:
        """在相邻格子 a、b 之间筑墙（两侧同步）。用于测试构造不连通情形。"""
        d = self._adjacent_direction(a, b)
        if d not in self.walls[a]:
            self.walls[a].add(d)
            self.walls[b].add(OPPOSITE[d])
            self._edges -= 1

    def _adjacent_direction(self, a: Cell, b: Cell) -> str:
        """返回从 a 指向 b 的方向名；若不相邻则抛异常。"""
        self._check(a)
        self._check(b)
        for d, (dr, dc) in DIRS.items():
            if (a[0] + dr, a[1] + dc) == b:
                return d
        raise ValueError(f"{a} 与 {b} 不相邻")

    # ---------- 性质判定 ----------

    def reachable_from(self, source: Cell) -> set[Cell]:
        """BFS 求从 source 可达的格子集合。"""
        seen = {source}
        queue = deque([source])
        while queue:
            cur = queue.popleft()
            for nb in self.open_neighbors(cur):
                if nb not in seen:
                    seen.add(nb)
                    queue.append(nb)
        return seen

    def connected(self) -> bool:
        return len(self.reachable_from(self.start)) == self.rows * self.cols

    def is_perfect(self) -> bool:
        """完美迷宫：任意两点恰有一条路径，等价于「连通 + 边数 = 格子数 - 1」（生成树）。"""
        return self.connected() and self._edges == self.rows * self.cols - 1

    def open_edge_set(self) -> frozenset[frozenset[Cell]]:
        """所有已打通的边（无向），用于确定性测试比较。"""
        edges = set()
        for cell in self.walls:
            r, c = cell
            for d in ("E", "S"):  # 每条边只从一侧统计一次
                nb = self.neighbor(cell, d)
                if nb is not None and d not in self.walls[cell]:
                    edges.add(frozenset((cell, nb)))
        return frozenset(edges)
