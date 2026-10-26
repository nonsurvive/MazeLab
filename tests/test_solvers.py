"""求解算法的单元测试。

核心验证思路（已知答案对照）：
1. 完美迷宫是生成树 → 任意两点间简单路径唯一 → 四种求解器必须返回
   完全相同的路径。这是一条强性质，能同时验证正确性和一致性。
2. 有环迷宫（braid 后）：BFS 与 A* 仍必须给出最优解且长度相等，
   DFS / 贪心允许更长，但不允许更短。
"""
import random

import pytest

from mazelab import Maze
from mazelab.generators import GENERATORS, braid
from mazelab.solvers import SOLVERS

GEN_NAMES = list(GENERATORS)
SOLVER_NAMES = list(SOLVERS)


def build(gen: str, size: int, seed: int, loops: float = 0.0) -> Maze:
    maze = Maze(size, size)
    for _ in GENERATORS[gen]["func"](maze, rng=random.Random(seed)):
        pass
    if loops > 0:
        for _ in braid(maze, loops, rng=random.Random(seed)):
            pass
    return maze


def assert_path_valid(maze: Maze, path):
    """路径合法性：从 start 到 end，每一步都相邻且无墙。"""
    assert path, "路径不应为空"
    assert path[0] == maze.start and path[-1] == maze.end
    for a, b in zip(path, path[1:]):
        assert not maze.has_wall(a, b), f"{a}->{b} 之间有墙，路径非法"
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, f"{a}->{b} 不相邻"


@pytest.mark.parametrize("gen", GEN_NAMES)
@pytest.mark.parametrize("seed", [0, 7, 42])
def test_perfect_maze_all_solvers_return_identical_path(gen, seed):
    """完美迷宫路径唯一：四种算法必须找到同一条路径（已知答案对照）。"""
    maze = build(gen, 13, seed)
    results = {name: SOLVERS[name]["func"](maze) for name in SOLVER_NAMES}
    reference = results["bfs"].path
    assert_path_valid(maze, reference)
    for name, r in results.items():
        assert r.path == reference, f"{gen}/seed={seed}: {name} 与 BFS 路径不一致"
        assert r.expanded >= 1 and r.frontier_peak >= 1 and r.seen >= r.expanded


@pytest.mark.parametrize("seed", [0, 7, 42])
def test_braided_maze_bfs_astar_optimal_dfs_greedy_not_shorter(seed):
    """有环迷宫：BFS/A* 最优且相等；DFS/贪心 >= 最优；所有路径合法。"""
    maze = build("backtracker", 15, seed, loops=0.6)
    results = {name: SOLVERS[name]["func"](maze) for name in SOLVER_NAMES}
    optimal = results["bfs"].path_len
    for name, r in results.items():
        assert_path_valid(maze, r.path)
        assert r.path_len >= optimal, f"{name} 路径短于 BFS 最优值，不可能"
    assert results["astar"].path_len == optimal, "A* 必须最优（启发式可采纳）"


def test_unreachable_end_returns_none():
    maze = build("backtracker", 7, 1)
    end = (6, 6)
    # 把终点彻底封死：终点在角落，只有 W、N 两个内部邻居
    maze.add_wall(end, (6, 5))
    maze.add_wall(end, (5, 6))
    for name in SOLVER_NAMES:
        r = SOLVERS[name]["func"](maze)
        assert r.path is None, f"{name} 应报告不可达"


def test_start_equals_end_trivial_path():
    maze = build("prim", 5, 2)
    for name in SOLVER_NAMES:
        r = SOLVERS[name]["func"](maze, start=(2, 2), end=(2, 2))
        assert r.path == [(2, 2)]
        assert r.path_len == 0


def test_one_cell_maze():
    maze = Maze(1, 1)
    for name in SOLVER_NAMES:
        r = SOLVERS[name]["func"](maze)
        assert r.path == [(0, 0)]


def test_endpoint_out_of_bounds_rejected():
    maze = build("backtracker", 5, 3)
    with pytest.raises(ValueError):
        SOLVERS["bfs"]["func"](maze, start=(0, 0), end=(9, 9))


def test_heuristics_prune_exploration_on_braided_maze():
    """有环迷宫上 A* 的启发式能剪枝：探索节点显著少于 BFS（实测约减半）。"""
    maze = build("backtracker", 51, 0, loops=0.6)
    bfs = SOLVERS["bfs"]["func"](maze)
    astar = SOLVERS["astar"]["func"](maze)
    assert astar.expanded < bfs.expanded


def test_greedy_explores_least_on_tree_maze():
    """树形迷宫上贪心只被启发值牵引，探索节点明显少于 BFS。"""
    maze = build("backtracker", 51, 11)
    bfs = SOLVERS["bfs"]["func"](maze)
    greedy = SOLVERS["greedy"]["func"](maze)
    assert greedy.expanded < bfs.expanded


def test_open_grid_dfs_stack_far_bigger_than_bfs_queue():
    """开阔网格（无内部墙）上 DFS 蛇形推进、分支在栈中积压：栈峰值远大于
    BFS 的对角波前（51x51 实测 DFS 1251 vs BFS 51）。"""
    open_maze = Maze(51, 51)
    for r in range(51):
        for c in range(51):
            for d in ("E", "S"):
                nb = open_maze.neighbor((r, c), d)
                if nb is not None and d in open_maze.walls[(r, c)]:
                    open_maze.carve((r, c), nb)
    dfs = SOLVERS["dfs"]["func"](open_maze)
    bfs = SOLVERS["bfs"]["func"](open_maze)
    assert dfs.frontier_peak > bfs.frontier_peak * 5


def test_perfect_maze_frontiers_are_small():
    """树形迷宫的走廊结构限制波前宽度：DFS/BFS 峰值都远小于格子总数
    （51x51 实测 DFS 29、BFS 10，而格子数 2601）——空间行为高度依赖图结构。"""
    maze = build("backtracker", 51, 4)
    n = maze.rows * maze.cols
    for name in ("dfs", "bfs"):
        r = SOLVERS[name]["func"](maze)
        assert r.frontier_peak < 0.05 * n
