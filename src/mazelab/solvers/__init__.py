"""迷宫求解算法。

四个算法在同一个 Maze 模型上运行，接口与指标口径完全一致
（见 base.SolveResult），这是对比实验成立的前提。
"""
from .base import SolveResult, manhattan
from .bfs import solve as bfs_solve
from .dfs import solve as dfs_solve
from .astar import solve as astar_solve
from .greedy import solve as greedy_solve

# name -> {"label": 中文显示名, "func": 求解函数}
SOLVERS: dict[str, dict] = {
    "bfs": {"label": "BFS 广度优先", "func": bfs_solve},
    "dfs": {"label": "DFS 深度优先", "func": dfs_solve},
    "astar": {"label": "A* 启发式", "func": astar_solve},
    "greedy": {"label": "贪心最佳优先", "func": greedy_solve},
}

__all__ = ["SOLVERS", "SolveResult", "manhattan"]
