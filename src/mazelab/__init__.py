"""MazeLab —— 迷宫生成、求解、可视化与对比实验。

仅使用 Python 标准库；界面基于 tkinter。
"""
from .maze import Maze, Cell, DIRS, DIR_ORDER
from .generators import GENERATORS, braid
from .solvers import SOLVERS, SolveResult

__version__ = "1.0.0"

__all__ = ["Maze", "Cell", "DIRS", "DIR_ORDER", "GENERATORS", "SOLVERS", "SolveResult", "braid"]
