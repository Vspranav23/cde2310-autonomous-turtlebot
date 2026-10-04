"""Render the simulated maze and the map built during test_maze_exploration to docs/sim_map.png."""

import importlib.util, io, contextlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

HERE = Path(__file__).resolve().parent
TEST = HERE / "test_maze_exploration.py"
OUT = HERE.parent.parent / "docs" / "sim_map.png"
spec = importlib.util.spec_from_file_location("t", TEST)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# Record every pose at which a LiDAR scan happens, and keep the final sim/maze
state = {"path": [], "sim": None}
orig_scan = m.MazeSimulatorHarness.update_lidar_scan
def scan(self, *a, **k):
    state["sim"] = self
    state["path"].append((self.robot_x, self.robot_y))
    return orig_scan(self, *a, **k)
m.MazeSimulatorHarness.update_lidar_scan = scan

with contextlib.redirect_stdout(io.StringIO()) as out:
    ok, _ = m.run_trials()
log = out.getvalue()
cov = [l for l in log.splitlines() if "Final Mapping Coverage" in l]
print("passed:", ok, "|", cov[0].strip() if cov else "")

sim = state["sim"]
maze = sim.maze
ext = [0, maze.width_m, 0, maze.height_m]
path = np.array(state["path"])
targets = [(t["id"], t["pos"]) for t in maze.thermal_targets]

fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))

def decorate(ax, title):
    for name, (tx, ty) in targets:
        ax.plot(tx, ty, marker="*", ms=18, color="#e8590c", mec="black", zorder=5)
        ax.annotate(name, (tx, ty), xytext=(6, 8), textcoords="offset points", fontsize=9, weight="bold")
    ax.plot(path[0, 0], path[0, 1], "o", ms=10, color="#2b8a3e", mec="black", zorder=5, label="Start")
    ax.set_title(title); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_xlim(0, maze.width_m); ax.set_ylim(0, maze.height_m); ax.set_aspect("equal")

# Ground truth: 0 free, 100 wall
gt = (maze.gt_grid == 100).astype(int)
axes[0].imshow(gt, origin="lower", extent=ext, cmap=ListedColormap(["#f8f9fa", "#212529"]))
decorate(axes[0], "Ground-truth maze (12 m x 12 m)")

# Discovered occupancy grid: -1 unknown, 0 free, 100 occupied
d = sim.discovered_map
disc = np.where(d == -1, 0, np.where(d == 0, 1, 2))
axes[1].imshow(disc, origin="lower", extent=ext, cmap=ListedColormap(["#adb5bd", "#ffffff", "#212529"]), vmin=0, vmax=2)
axes[1].plot(path[:, 0], path[:, 1], "-", color="#1c7ed6", lw=1.5, alpha=0.8, label="Robot path")
axes[1].plot(path[:, 0], path[:, 1], ".", color="#1c7ed6", ms=4)
decorate(axes[1], "Map built by robot (grey = unknown)")
axes[1].legend(loc="upper right", fontsize=8)

fig.tight_layout()
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT, dpi=130)
print(f"saved {OUT}")
