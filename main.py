"""MazeLab 程序入口。

    python main.py                 # 启动图形界面
    python main.py --help          # 查看命令行用法
    python main.py --size 31 --solve all --seed 42 --ascii
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from mazelab.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
