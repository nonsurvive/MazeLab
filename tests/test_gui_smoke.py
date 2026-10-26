"""GUI 冒烟测试：在无显示环境下自动跳过；验证界面可以构建、生成、求解。"""
import pytest

tkinter = pytest.importorskip("tkinter")


def test_gui_smoke():
    try:
        root = tkinter.Tk()
    except tkinter.TclError:
        pytest.skip("无可用显示环境，跳过 GUI 测试")
    try:
        from mazelab.gui import MazeApp
        app = MazeApp(root)

        app.loop_scale.set(30)          # 带环路生成，覆盖 braid 分支
        app.regenerate()
        assert app.phase == "generating"
        app.finish_generation_now()
        assert app.phase == "idle"
        assert app.maze.is_perfect() or app.maze.connected()

        app.solve_now()
        assert app.solve_result is not None
        assert app.solve_result.path is not None

        app.run_comparison()            # 一键对比不抛异常
        app._set_endpoint(type("E", (), {"x": app.ox + 5 * app.cell_px,
                                         "y": app.oy + 5 * app.cell_px})(),
                          is_start=True)  # 模拟点击换起点
        root.update()
    finally:
        root.destroy()
