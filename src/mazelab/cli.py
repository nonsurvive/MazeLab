"""命令行入口：演示单个迷宫、对比全部算法、运行批量实验。

不带参数运行 = 启动图形界面；带任意参数 = 命令行模式。
"""
from __future__ import annotations

import argparse
import random
import sys

from .maze import Maze
from .generators import GENERATORS, braid
from .solvers import SOLVERS
from .render import to_ascii
from .bench import run_bench, aggregate_markdown, to_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="MazeLab",
        description="迷宫生成与求解：可视化（无参数启动）或命令行实验。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--gui", action="store_true", help="强制启动图形界面")
    parser.add_argument("--size", type=int, default=None, help="正方形迷宫边长（等价于同时指定 rows=cols）")
    parser.add_argument("--rows", type=int, default=21, help="行数（格子数）")
    parser.add_argument("--cols", type=int, default=21, help="列数（格子数）")
    parser.add_argument("--gen", choices=list(GENERATORS), default="backtracker", help="生成算法")
    parser.add_argument("--loops", type=float, default=0.0, help="环路比例 0~1，>0 时迷宫含环")
    parser.add_argument("--seed", type=int, default=None, help="随机种子（缺省随机，运行时打印以便复现）")
    parser.add_argument("--solve", default="all",
                        choices=list(SOLVERS) + ["all", "none"], help="求解算法")
    parser.add_argument("--ascii", action="store_true", help="打印迷宫字符画（单算法求解时叠加路径）")
    parser.add_argument("--bench", action="store_true", help="运行批量对比实验")
    parser.add_argument("--trials", type=int, default=20, help="bench 每组配置的迷宫数量")
    parser.add_argument("--bench-csv", metavar="PATH", help="bench 原始数据输出 CSV 路径")
    parser.add_argument("--bench-md", metavar="PATH", help="bench 汇总表输出 Markdown 路径")
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.size is not None:
        args.rows = args.cols = args.size
    if args.bench:
        return _run_bench(args)

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)
    print(f"迷宫 {args.rows}x{args.cols} | 生成算法: {args.gen} | "
          f"环路比例: {args.loops} | 随机种子: {seed}（可用 --seed 复现）\n")

    maze = Maze(args.rows, args.cols)
    for _ in GENERATORS[args.gen]["func"](maze, rng=rng):
        pass
    if args.loops > 0:
        for _ in braid(maze, args.loops, rng=rng):
            pass
    print(f"性质检查: 连通={maze.connected()}, 完美迷宫={maze.is_perfect()}, "
          f"打通边数={maze.edges()}（完美迷宫应为 {args.rows * args.cols - 1}）\n")

    if args.solve == "none":
        if args.ascii:
            print(to_ascii(maze))
        return 0

    if args.solve == "all":
        _print_comparison(maze)
        return 0

    func = SOLVERS[args.solve]["func"]
    result = func(maze)
    print(f"[{SOLVERS[args.solve]['label']}] 探索节点 {result.expanded} | "
          f"标记节点 {result.seen} | 峰值前沿 {result.frontier_peak} | "
          f"路径长度 {result.path_len}")
    if result.path is None:
        print("结论：终点不可达。")
    if args.ascii:
        print()
        print(to_ascii(maze, result.path))
    return 0


def _print_comparison(maze: Maze) -> None:
    import time

    rows = []
    for name, info in SOLVERS.items():
        best, result = float("inf"), None
        for _ in range(5):  # 重复 5 次取最小耗时，减少噪声
            t0 = time.perf_counter()
            result = info["func"](maze)
            best = min(best, (time.perf_counter() - t0) * 1000)
        rows.append((info["label"], result, best))

    print(f"{'算法':<14}{'探索节点':>8}{'标记节点':>8}{'峰值前沿':>8}{'路径长度':>8}{'耗时ms':>10}")
    for label, r, ms in rows:
        path_text = str(r.path_len) if r.path is not None else "不可达"
        print(f"{label:<14}{r.expanded:>8}{r.seen:>8}{r.frontier_peak:>8}{path_text:>8}{ms:>10.3f}")
    if maze.is_perfect():
        print("\n说明：完美迷宫任意两点路径唯一，故各算法路径长度相同（DFS 亦最优）；"
              "差异体现在探索规模与前沿峰值（空间开销）。")
    else:
        print("\n说明：本迷宫含环路，BFS/A* 给出最短路；DFS/贪心可能更长——"
              "对比「路径长度」与「探索节点」可见启发式与最优性的取舍。")


def _run_bench(args) -> int:
    print(f"运行实验：生成算法 backtracker/prim，规模 15/31/51/101，"
          f"每组 {args.trials} 个迷宫 × 4 种求解算法……")
    rows = run_bench(trials=args.trials, loops=args.loops if 0 < args.loops <= 1 else 0.0)
    table = aggregate_markdown(rows)
    print()
    print(table)

    if args.bench_csv:
        with open(args.bench_csv, "w", encoding="utf-8") as f:
            f.write(to_csv(rows) + "\n")
        print(f"\n原始数据已写入 {args.bench_csv}")
    if args.bench_md:
        with open(args.bench_md, "w", encoding="utf-8") as f:
            f.write(table + "\n")
        print(f"汇总表已写入 {args.bench_md}")
    return 0


def main(argv: list[str] | None = None) -> int:
    # 无参数（或 --gui）时启动图形界面
    if argv is None:
        argv = sys.argv[1:]
    if not argv or "--gui" in argv:
        from .gui import run
        run()
        return 0
    return run_cli(argv)
