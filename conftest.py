"""pytest 配置：把 src 目录加入导入路径，测试即可直接 import mazelab。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
