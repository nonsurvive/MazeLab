"""tkinter 图形界面：迷宫生成动画、求解动画、指标面板与一键算法对比。

设计：核心算法在 generators/solvers 包中，GUI 只负责「事件回放」——
算法以事件流（carve/visit/frontier）输出过程，界面按帧应用事件并着色，
核心逻辑与界面完全分离。
"""
from __future__ import annotations

import itertools
import random
import time

import tkinter as tk
from tkinter import ttk

from .maze import Maze
from .generators import GENERATORS, braid
from .solvers import SOLVERS

CANVAS_W, CANVAS_H = 880, 620
PAD = 8

C_UNCARVED = "#3b4252"   # 未拆墙的格子（生成前的实心区域）
C_CARVED = "#eceff4"     # 已打通
C_VISITED = "#9ec5fe"    # 求解时已访问
C_FRONTIER = "#ffe08a"   # 求解时在前沿
C_ACTIVE = "#f5a623"     # 生成动画的当前格子
C_START = "#2eb872"
C_END = "#e05252"
C_WALL = "#2f3640"
C_PATH = "#e8590c"

TICK_MS = 15  # 动画帧间隔


class MazeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("MazeLab — 迷宫生成与求解可视化")
        root.resizable(False, False)

        self.maze: Maze | None = None
        self.phase = "empty"            # empty / generating / idle / solving
        self.paused = False
        self.gen_iter = None            # 生成器事件流
        self.solve_events: list = []
        self.solve_idx = 0
        self.solve_result = None
        self.cell_ids: dict = {}        # cell -> canvas 矩形 id
        self.path_id = None
        self._active_cell = None
        self.cell_px = 10
        self.ox = PAD
        self.oy = PAD

        self._build_controls()
        self._build_canvas()
        self._build_status()
        self.root.after(TICK_MS, self._tick)

    # ---------- 界面搭建 ----------

    def _build_controls(self):
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side=tk.TOP, fill=tk.X)

        self.gen_labels = {v["label"]: k for k, v in GENERATORS.items()}
        self.solve_labels = {v["label"]: k for k, v in SOLVERS.items()}

        ttk.Label(bar, text="生成算法").grid(row=0, column=0, padx=2)
        self.gen_box = ttk.Combobox(bar, values=list(self.gen_labels), state="readonly", width=11)
        self.gen_box.current(0)
        self.gen_box.grid(row=0, column=1, padx=2)

        ttk.Label(bar, text="大小").grid(row=0, column=2, padx=(10, 2))
        self.size_var = tk.StringVar(value="21")
        ttk.Spinbox(bar, from_=3, to=121, textvariable=self.size_var, width=5).grid(row=0, column=3)

        ttk.Label(bar, text="种子").grid(row=0, column=4, padx=(10, 2))
        self.seed_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.seed_var, width=8).grid(row=0, column=5)
        self.seed_var.set("2026")

        ttk.Label(bar, text="环路%").grid(row=0, column=6, padx=(10, 2))
        self.loop_scale = tk.Scale(bar, from_=0, to=100, orient=tk.HORIZONTAL,
                                   length=110, showvalue=False)
        self.loop_scale.grid(row=0, column=7)

        ttk.Button(bar, text="生成迷宫", command=self.regenerate).grid(row=0, column=8, padx=10)

        ttk.Label(bar, text="求解算法").grid(row=1, column=0, padx=2, pady=(6, 0))
        self.solve_box = ttk.Combobox(bar, values=list(self.solve_labels), state="readonly", width=11)
        self.solve_box.current(2)  # 默认 A*
        self.solve_box.grid(row=1, column=1, pady=(6, 0))

        ttk.Label(bar, text="速度").grid(row=1, column=2, padx=(10, 2), pady=(6, 0))
        self.speed_scale = tk.Scale(bar, from_=1, to=100, orient=tk.HORIZONTAL,
                                    length=110, showvalue=False)
        self.speed_scale.set(30)
        self.speed_scale.grid(row=1, column=3, pady=(6, 0))

        ttk.Button(bar, text="求解动画", command=self.solve_animated).grid(row=1, column=4, padx=10, pady=(6, 0))
        self.pause_btn = ttk.Button(bar, text="暂停", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_btn.grid(row=1, column=5, pady=(6, 0))
        ttk.Button(bar, text="清除标记", command=self.clear_overlays).grid(row=1, column=6, pady=(6, 0))
        ttk.Button(bar, text="一键对比", command=self.run_comparison).grid(row=1, column=7, pady=(6, 0))

    def _build_canvas(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=CANVAS_H,
                                bg="white", highlightthickness=1,
                                highlightbackground="#aaaaaa")
        self.canvas.pack(side=tk.TOP, padx=PAD, pady=(0, 4))
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.create_text(CANVAS_W // 2, CANVAS_H // 2,
                                text="点击「生成迷宫」开始\n左键设起点，右键设终点",
                                font=("Microsoft YaHei UI", 13), fill="#888888")

    def _build_status(self):
        self.status_var = tk.StringVar(value="就绪。先生成迷宫，再求解。")
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                          justify=tk.LEFT, font=("Consolas", 10), bg="#f4f4f4")
        status.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- 生成迷宫 ----------

    def regenerate(self):
        try:
            n = int(self.size_var.get())
            if not 3 <= n <= 121:
                raise ValueError
        except ValueError:
            self.status_var.set("大小必须是 3~121 的整数。")
            return

        seed_text = self.seed_var.get().strip()
        try:
            seed = int(seed_text) if seed_text else random.randrange(2**31)
        except ValueError:
            self.status_var.set("种子必须是整数，或留空表示随机。")
            return

        gen_key = self.gen_labels[self.gen_box.get()]
        loops = self.loop_scale.get() / 100.0

        self.canvas.delete("all")
        self.maze = Maze(n, n)
        self.cell_px = max(3, min(30, min((CANVAS_W - 2 * PAD) // n, (CANVAS_H - 2 * PAD) // n)))
        self.ox = (CANVAS_W - self.cell_px * n) // 2
        self.oy = (CANVAS_H - self.cell_px * n) // 2
        self.cell_ids.clear()
        self.path_id = None
        for r in range(n):
            for c in range(n):
                x0 = self.ox + c * self.cell_px
                y0 = self.oy + r * self.cell_px
                self.cell_ids[(r, c)] = self.canvas.create_rectangle(
                    x0, y0, x0 + self.cell_px, y0 + self.cell_px,
                    fill=C_UNCARVED, outline="")

        main_gen = GENERATORS[gen_key]["func"](self.maze, rng=random.Random(seed))
        self.gen_iter = itertools.chain(
            main_gen, braid(self.maze, loops, rng=random.Random(seed)) if loops > 0 else iter(())
        )
        self.phase = "generating"
        self.paused = False
        self.pause_btn.config(text="暂停", state=tk.NORMAL)
        self.solve_events, self.solve_idx, self.solve_result = [], 0, None
        self.status_var.set(f"生成中… 算法={GENERATORS[gen_key]['label']} 大小={n}x{n} 种子={seed} 环路={loops:.0%}")

    def _finish_generation(self):
        self._paint_active(None)
        self._draw_walls()
        self._draw_markers()
        self.phase = "idle"
        self.pause_btn.config(state=tk.DISABLED, text="暂停")
        edges = self.maze.edges()
        perfect = self.maze.is_perfect()
        extra = f"（环路比例 {(self.loop_scale.get()) / 100:.0%}，已含 {edges - self.maze.rows * self.maze.cols + 1} 条附加边）" if not perfect else ""
        self.status_var.set(
            f"生成完成：格子 {self.maze.rows}x{self.maze.cols}，打通边数 {edges}，完美迷宫={perfect}{extra}。"
            f"左键设起点、右键设终点，然后「求解动画」。")

    def _draw_walls(self):
        """生成结束后一次性画出全部墙线。n 最大 121，总量约 3 万条线，可接受。"""
        n, s = self.maze.rows, self.cell_px
        w = max(1, 5 - self.cell_px // 6)  # 格子越小线越细
        for r in range(n):
            for c in range(n):
                x0, y0 = self.ox + c * s, self.oy + r * s
                cell = (r, c)
                walls = self.maze.walls[cell]
                if "N" in walls:
                    self.canvas.create_line(x0, y0, x0 + s, y0, fill=C_WALL, width=w)
                if "W" in walls:
                    self.canvas.create_line(x0, y0, x0, y0 + s, fill=C_WALL, width=w)
        # 右、下边界
        x1, y1 = self.ox + n * s, self.oy + n * s
        self.canvas.create_line(x1, self.oy, x1, y1, fill=C_WALL, width=w)
        self.canvas.create_line(self.ox, y1, x1, y1, fill=C_WALL, width=w)

    def _draw_markers(self):
        for cell, color in ((self.maze.start, C_START), (self.maze.end, C_END)):
            self._paint(cell, color)

    # ---------- 求解 ----------

    def solve_animated(self):
        if self.phase not in ("idle",):
            self.status_var.set("请先完成迷宫生成（正在生成/求解时不接受新的求解）。")
            return
        solver_key = self.solve_labels[self.solve_box.get()]
        self.clear_overlays()
        events = []
        t0 = time.perf_counter()
        result = SOLVERS[solver_key]["func"](self.maze, on_event=lambda k, c: events.append((k, c)))
        ms = (time.perf_counter() - t0) * 1000
        self.solve_events, self.solve_idx, self.solve_result = events, 0, result
        self.pending_label = SOLVERS[solver_key]["label"]
        self.pending_ms = ms
        self.phase = "solving"
        self.paused = False
        self.pause_btn.config(text="暂停", state=tk.NORMAL)

    def _finish_solving(self):
        self._draw_path()
        r = self.solve_result
        if r.path is None:
            text = f"求解完成 [{self.pending_label}]：终点不可达！探索 {r.expanded}，标记 {r.seen}，耗时 {self.pending_ms:.2f} ms"
        else:
            text = (f"求解完成 [{self.pending_label}]：路径长度 {r.path_len} 步 | 探索 {r.expanded} | "
                    f"标记 {r.seen} | 峰值前沿 {r.frontier_peak} | 耗时 {self.pending_ms:.2f} ms")
        self.status_var.set(text)
        self.phase = "idle"
        self.pause_btn.config(state=tk.DISABLED, text="暂停")

    def _draw_path(self):
        r = self.solve_result
        if r is None or not r.path:
            return
        pts = []
        for (row, col) in r.path:
            pts.extend((self.ox + (col + 0.5) * self.cell_px,
                        self.oy + (row + 0.5) * self.cell_px))
        width = max(2, self.cell_px // 4)
        self.path_id = self.canvas.create_line(*pts, fill=C_PATH, width=width,
                                               capstyle=tk.ROUND, joinstyle=tk.ROUND)

    # ---------- 一键对比 ----------

    def run_comparison(self):
        if self.phase != "idle":
            self.status_var.set("请先生成迷宫（并在求解动画结束后）再对比。")
            return
        self.clear_overlays()
        lines = [f"{'算法':<12}{'探索':>7}{'标记':>7}{'峰前沿':>7}{'路径':>7}{'耗时ms':>10}"]
        for name, info in SOLVERS.items():
            best, result = float("inf"), None
            for _ in range(5):
                t0 = time.perf_counter()
                result = info["func"](self.maze)
                best = min(best, (time.perf_counter() - t0) * 1000)
            p = str(result.path_len) if result.path is not None else "不可达"
            lines.append(f"{info['label']:<12}{result.expanded:>7}{result.seen:>7}"
                         f"{result.frontier_peak:>7}{p:>7}{best:>10.2f}")
        self.status_var.set(" | ".join(l.strip() for l in lines[:1]) + "\n" + "\n".join(lines[1:]))

    # ---------- 交互 ----------

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="继续" if self.paused else "暂停")

    def clear_overlays(self):
        if self.maze is None or self.phase not in ("idle",):
            return
        if self.path_id is not None:
            self.canvas.delete(self.path_id)
            self.path_id = None
        for cell, cid in self.cell_ids.items():
            color = C_CARVED
            if cell == self.maze.start:
                color = C_START
            elif cell == self.maze.end:
                color = C_END
            self.canvas.itemconfig(cid, fill=color)
        self.solve_events, self.solve_idx, self.solve_result = [], 0, None

    def on_left_click(self, event):
        self._set_endpoint(event, is_start=True)

    def on_right_click(self, event):
        self._set_endpoint(event, is_start=False)

    def _set_endpoint(self, event, is_start: bool):
        if self.phase != "idle" or self.maze is None:
            return
        c = (event.x - self.ox) // self.cell_px
        r = (event.y - self.oy) // self.cell_px
        cell = (int(r), int(c))
        if not self.maze.in_bounds(cell):
            return
        if is_start:
            self.maze.start = cell
        else:
            self.maze.end = cell
        self.clear_overlays()
        self._draw_markers()

    # ---------- 动画循环 ----------

    def _tick(self):
        try:
            if not self.paused:
                if self.phase == "generating":
                    self._tick_generate()
                elif self.phase == "solving":
                    self._tick_solve()
        finally:
            self.root.after(TICK_MS, self._tick)

    def _tick_generate(self):
        k = self.speed_scale.get()
        for _ in range(k):
            try:
                kind, *payload = next(self.gen_iter)
            except StopIteration:
                self._finish_generation()
                return
            if kind == "carve":
                a, b = payload
                self._paint(a, C_CARVED)
                self._paint(b, C_CARVED)
                self._paint_active(b)
            elif kind == "active":
                self._paint_active(payload[0])

    def _tick_solve(self):
        k = self.speed_scale.get()
        for _ in range(k):
            if self.solve_idx >= len(self.solve_events):
                self._finish_solving()
                return
            kind, cell = self.solve_events[self.solve_idx]
            self.solve_idx += 1
            if kind == "visit":
                self._paint(cell, C_VISITED)
            elif kind == "frontier":
                self._paint(cell, C_FRONTIER)

    # ---------- 绘制辅助 ----------

    def _paint(self, cell, color):
        cid = self.cell_ids.get(cell)
        if cid is not None:
            self.canvas.itemconfig(cid, fill=color)

    def _paint_active(self, cell):
        if self._active_cell is not None:
            self._paint(self._active_cell, C_CARVED)
        self._active_cell = cell
        if cell is not None:
            self._paint(cell, C_ACTIVE)

    # ---------- 测试辅助（同步跑完全部动画） ----------

    def finish_generation_now(self):
        if self.phase == "generating":
            self.speed_scale.set(10**9)
            while self.phase == "generating":
                self._tick_generate()

    def solve_now(self):
        if self.phase == "idle":
            self.solve_animated()
            self.speed_scale.set(10**9)
            while self.phase == "solving":
                self._tick_solve()


def run():
    root = tk.Tk()
    MazeApp(root)
    root.mainloop()
