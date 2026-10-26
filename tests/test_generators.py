"""生成算法的单元测试：完美迷宫性质、确定性、braid 加环。"""
import random

import pytest

from mazelab import Maze
from mazelab.generators import GENERATORS, braid

GEN_NAMES = list(GENERATORS)
# 覆盖 1x1、非方阵、常规方阵等边界形状
SHAPES = [(1, 1), (2, 3), (7, 7), (15, 4), (21, 21)]


def build(gen: str, rows: int, cols: int, seed: int) -> Maze:
    maze = Maze(rows, cols)
    for _ in GENERATORS[gen]["func"](maze, rng=random.Random(seed)):
        pass
    return maze


@pytest.mark.parametrize("gen", GEN_NAMES)
@pytest.mark.parametrize("rows,cols", SHAPES)
def test_generates_perfect_maze(gen, rows, cols):
    maze = build(gen, rows, cols, seed=42)
    assert maze.connected(), f"{gen}: 所有格子必须连通"
    assert maze.edges() == rows * cols - 1, f"{gen}: 生成树边数应为 格子数-1"
    assert maze.is_perfect()


@pytest.mark.parametrize("gen", GEN_NAMES)
def test_deterministic_with_same_seed(gen):
    m1 = build(gen, 13, 13, seed=7)
    m2 = build(gen, 13, 13, seed=7)
    assert m1.open_edge_set() == m2.open_edge_set()


@pytest.mark.parametrize("gen", GEN_NAMES)
def test_different_seeds_differ(gen):
    m1 = build(gen, 21, 21, seed=1)
    m2 = build(gen, 21, 21, seed=2)
    assert m1.open_edge_set() != m2.open_edge_set()


@pytest.mark.parametrize("gen", GEN_NAMES)
def test_boundary_walls_never_opened(gen):
    maze = build(gen, 9, 9, seed=3)
    # 边界格子向外的墙必须始终存在（生成算法不允许拆边界）
    for c in range(9):
        assert "N" in maze.walls[(0, c)]
        assert "S" in maze.walls[(8, c)]
    for r in range(9):
        assert "W" in maze.walls[(r, 0)]
        assert "E" in maze.walls[(r, 8)]


def test_braid_p1_removes_all_dead_ends():
    maze = build("backtracker", 11, 11, seed=5)
    assert maze.dead_ends(), "完美迷宫应当有死胡同"
    for _ in braid(maze, 1.0, rng=random.Random(5)):
        pass
    assert maze.edges() > 11 * 11 - 1  # 加环后边数超过生成树
    assert not maze.is_perfect()
    min_degree = min(maze.degree(cell) for cell in maze.walls)
    assert min_degree >= 2, "p=1 时所有死胡同都应被消除"


def test_braid_partial_and_deterministic():
    m1 = build("prim", 13, 13, seed=9)
    m2 = build("prim", 13, 13, seed=9)
    for _ in braid(m1, 0.5, rng=random.Random(9)):
        pass
    for _ in braid(m2, 0.5, rng=random.Random(9)):
        pass
    assert m1.open_edge_set() == m2.open_edge_set()
    assert m1.edges() >= 13 * 13 - 1


def test_braid_invalid_probability():
    maze = build("backtracker", 5, 5, seed=1)
    with pytest.raises(ValueError):
        list(braid(maze, 1.5, rng=random.Random(1)))
