"""Maze 数据模型的单元测试。"""
import pytest

from mazelab import Maze
from mazelab.render import to_ascii


def test_invalid_size_rejected():
    with pytest.raises(ValueError):
        Maze(0, 5)
    with pytest.raises(ValueError):
        Maze(3, 0)


def test_initial_maze_fully_walled():
    maze = Maze(3, 3)
    assert maze.edges() == 0
    assert not maze.connected()
    assert not maze.is_perfect()
    # 每个格子四面都是墙，无路可走
    for cell in maze.walls:
        assert maze.open_neighbors(cell) == []
    assert maze.start == (0, 0) and maze.end == (2, 2)


def test_neighbor_out_of_bounds_returns_none():
    maze = Maze(2, 2)
    assert maze.neighbor((0, 0), "N") is None
    assert maze.neighbor((0, 0), "W") is None
    assert maze.neighbor((1, 1), "S") is None
    assert maze.neighbor((1, 1), "E") is None
    assert maze.neighbor((0, 0), "E") == (0, 1)
    assert maze.neighbor((0, 0), "S") == (1, 0)


def test_carve_requires_adjacent_cells():
    maze = Maze(3, 3)
    with pytest.raises(ValueError):
        maze.carve((0, 0), (2, 2))  # 不相邻


def test_carve_boundary_rejected():
    maze = Maze(2, 2)
    with pytest.raises(ValueError):
        maze.carve((0, 0), (-1, 0))  # 越界


def test_carve_twice_rejected():
    maze = Maze(2, 2)
    maze.carve((0, 0), (0, 1))
    with pytest.raises(ValueError):
        maze.carve((0, 0), (0, 1))


def test_carve_updates_both_sides_and_edge_count():
    maze = Maze(2, 2)
    maze.carve((0, 0), (0, 1))  # E 方向
    assert "E" not in maze.walls[(0, 0)]
    assert "W" not in maze.walls[(0, 1)]
    assert not maze.has_wall((0, 0), (0, 1))
    assert not maze.has_wall((0, 1), (0, 0))  # 对称
    assert maze.edges() == 1
    maze.add_wall((0, 0), (0, 1))
    assert maze.has_wall((0, 1), (0, 0))
    assert maze.edges() == 0


def test_out_of_bounds_cell_raises():
    maze = Maze(2, 2)
    with pytest.raises(ValueError):
        maze.open_neighbors((5, 5))
    with pytest.raises(ValueError):
        maze.neighbor((5, 5), "E")


def test_perfect_flag_after_generation():
    from mazelab.generators import GENERATORS
    import random
    for gen in GENERATORS:
        maze = Maze(9, 9)
        for _ in GENERATORS[gen]["func"](maze, rng=random.Random(1)):
            pass
        assert maze.is_perfect(), f"{gen} 应生成完美迷宫"
        assert maze.edges() == 9 * 9 - 1


def test_start_end_validation():
    with pytest.raises(ValueError):
        Maze(3, 3, start=(0, 9))


def test_ascii_render_shape():
    maze = Maze(4, 6)
    text = to_ascii(maze)
    lines = text.split("\n")
    assert len(lines) == 2 * 4 + 1
    assert all(len(line) == 2 * 6 + 1 for line in lines)
    assert lines[0].startswith("+")
    assert "S" in text and "E" in text


def test_open_edge_set_counts_each_edge_once():
    maze = Maze(3, 3)
    maze.carve((0, 0), (0, 1))
    maze.carve((0, 1), (0, 2))
    edge_set = maze.open_edge_set()
    assert len(edge_set) == 2
    assert frozenset({(0, 0), (0, 1)}) in edge_set
