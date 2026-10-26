"""ASCII 渲染：把迷宫画成字符画，供命令行演示与测试快照。"""
from __future__ import annotations

from .maze import Maze, Cell


def to_ascii(maze: Maze, path: list[Cell] | None = None) -> str:
    """渲染为 (2*rows+1) × (2*cols+1) 的字符画。

    ``+`` 角点，``-``/``|`` 墙，空格为通路。path 非空时用 ``*`` 标出路径格子，
    起点终点分别标 ``S``、``E``。
    """
    height, width = 2 * maze.rows + 1, 2 * maze.cols + 1
    grid = [[" "] * width for _ in range(height)]

    for r in range(maze.rows + 1):
        for c in range(maze.cols + 1):
            grid[2 * r][2 * c] = "+"
    for r in range(maze.rows):
        for c in range(maze.cols):
            cell = (r, c)
            if "E" in maze.walls[cell] and c + 1 < maze.cols:
                grid[2 * r + 1][2 * c + 2] = "|"
            if "S" in maze.walls[cell] and r + 1 < maze.rows:
                grid[2 * r + 2][2 * c + 1] = "-"
            # 顶行/左列的边界墙
            if r == 0:
                grid[0][2 * c + 1] = "-"
            if c == 0:
                grid[2 * r + 1][0] = "|"
        # 底行与右列边界
        grid[2 * maze.rows][2 * c + 1] = "-"
        grid[2 * r + 1][2 * maze.cols] = "|"

    marks = {maze.start: "S", maze.end: "E"}
    if path:
        for cell in path:
            if cell not in marks:
                marks[cell] = "*"
    for (r, c), ch in marks.items():
        grid[2 * r + 1][2 * c + 1] = ch

    return "\n".join("".join(row) for row in grid)
