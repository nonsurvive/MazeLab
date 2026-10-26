"""求解算法的公共定义。"""

from __future__ import annotations

from dataclasses import dataclass

from ..maze import Maze, Cell


@dataclass
class SolveResult:
    """一次求解的完整指标。

    expanded：从前沿数据结构中取出并真正展开（检查其邻居）的节点数，
              即「工作量」的主指标。
    seen：    被放入过前沿/标记过的不同节点总数，近似内存占用。
    frontier_peak：前沿数据结构的最大元素个数，直接反映空间开销差异
              （DFS 的栈很浅，BFS 的队列很宽）。
    """

    path: list[Cell] | None
    expanded: int
    seen: int
    frontier_peak: int

    @property
    def path_len(self) -> int:
        """路径步数（边数）；不可达为 0。"""
        return len(self.path) - 1 if self.path else 0


def reconstruct(parent: dict[Cell, Cell], start: Cell, end: Cell) -> list[Cell]:
    """沿 parent 指针从终点回溯到起点，返回 start→end 的路径。"""
    path = [end]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def manhattan(a: Cell, b: Cell) -> int:
    """曼哈顿距离。四邻域网格上每步最多靠近 1，因此该启发式可采纳（不会高估）。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def check_endpoints(maze: Maze, start: Cell | None, end: Cell | None) -> tuple[Cell, Cell]:
    s = start if start is not None else maze.start
    e = end if end is not None else maze.end
    if not (maze.in_bounds(s) and maze.in_bounds(e)):
        raise ValueError("起点/终点越界")
    return s, e


def unreachable(expanded: int, seen: int, peak: int) -> SolveResult:
    return SolveResult(path=None, expanded=expanded, seen=seen, frontier_peak=peak)
