"""对比实验：在不同规模、不同生成算法的迷宫上批量运行各求解算法。

所有迷宫由固定种子生成，结果可复现。计时只包住纯算法调用
（on_event=None，无动画回调开销），每个配置重复 REPEAT 次取最小值，
以降低系统调度噪声。
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .maze import Maze
from .generators import GENERATORS, braid
from .solvers import SOLVERS

REPEAT = 5  # 每个配置重复求解次数，取最小耗时


@dataclass
class BenchRow:
    gen: str
    size: int
    seed: int
    loops: float
    solver: str
    expanded: int
    seen: int
    frontier_peak: int
    path_len: int
    time_ms: float


def build_maze(gen: str, size: int, seed: int, loops: float = 0.0) -> Maze:
    """按 (生成算法, 边长, 种子, 环路比例) 构造迷宫。"""
    maze = Maze(size, size)
    func = GENERATORS[gen]["func"]
    for _ in func(maze, rng=random.Random(seed)):
        pass
    if loops > 0:
        for _ in braid(maze, loops, rng=random.Random(seed)):
            pass
    return maze


def run_bench(sizes=(15, 31, 51, 101), gens=("backtracker", "prim"),
              solvers=("bfs", "dfs", "astar", "greedy"),
              trials=20, loops=0.0, seed0=2026) -> list[BenchRow]:
    rows: list[BenchRow] = []
    for gen in gens:
        for size in sizes:
            for t in range(trials):
                seed = seed0 + t
                maze = build_maze(gen, size, seed, loops)
                for solver in solvers:
                    func = SOLVERS[solver]["func"]
                    best = float("inf")
                    result = None
                    for _ in range(REPEAT):
                        t0 = time.perf_counter()
                        result = func(maze)
                        dt = (time.perf_counter() - t0) * 1000
                        best = min(best, dt)
                    rows.append(BenchRow(
                        gen=gen, size=size, seed=seed, loops=loops, solver=solver,
                        expanded=result.expanded, seen=result.seen,
                        frontier_peak=result.frontier_peak,
                        path_len=result.path_len, time_ms=round(best, 3),
                    ))
    return rows


def aggregate_markdown(rows: list[BenchRow]) -> str:
    """按 (生成算法, 规模, 求解算法) 聚合：expanded/path_len/time 取均值。"""
    groups: dict[tuple, list[BenchRow]] = {}
    for row in rows:
        groups.setdefault((row.gen, row.size, row.solver), []).append(row)

    lines = [
        "| 生成算法 | 规模 | 求解算法 | 探索节点均值 | 路径长度均值 | 峰值前沿均值 | 平均耗时 (ms) |",
        "| :--- | ---: | :--- | ---: | ---: | ---: | ---: |",
    ]
    for (gen, size, solver), rs in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
        n = len(rs)
        lines.append(
            f"| {gen} | {size}×{size} | {solver} "
            f"| {sum(r.expanded for r in rs) / n:.0f} "
            f"| {sum(r.path_len for r in rs) / n:.1f} "
            f"| {sum(r.frontier_peak for r in rs) / n:.0f} "
            f"| {sum(r.time_ms for r in rs) / n:.3f} |"
        )
    return "\n".join(lines)


def to_csv(rows: list[BenchRow]) -> str:
    header = "gen,size,seed,loops,solver,expanded,seen,frontier_peak,path_len,time_ms"
    lines = [header]
    for r in rows:
        lines.append(f"{r.gen},{r.size},{r.seed},{r.loops},{r.solver},"
                     f"{r.expanded},{r.seen},{r.frontier_peak},{r.path_len},{r.time_ms}")
    return "\n".join(lines)
