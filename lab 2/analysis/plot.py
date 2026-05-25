"""纯ALOHA仿真结果的绘图和可視化。

生成四个标准图表:
  1. P-S曲线:         发送速率λ vs.信道利用率S
  2. N-S曲线:          标签计数vs.信道利用率
  3. 碰撞率:     λ vs.碰撞比率
  4. 时间轴图表:     按数据包甄特图式碰撞视图
"""

import json
import os
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # 非互动式后端
import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------------
# 调色板
# ---------------------------------------------------------------------------
SUCCESS_COLOR = "#2ecc71"
PARTIAL_COLOR = "#f39c12"
FULL_COLOR = "#e74c3c"


# ---------------------------------------------------------------------------
# 1. P-S曲线:  λ vs信道利用率
# ---------------------------------------------------------------------------
def plot_ps_curve(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制提供的负载/发送速率vs.信道利用率。

    参数:
        csv_path: 一个CSV文件的路径,具有列[tag_num,lambda,success,
                  collision,utilization]用于多个运行。
        out_path: PNG文件的目标。

    返回:
        保存的图表的路径。
    """
    if out_path is None:
        out_path = os.path.join(
            os.path.dirname(csv_path), "..", "plots", "ps_curve.png"
        )

    df = pd.read_csv(csv_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    # 按λ分组并平均利用率
    grouped = df.groupby("lambda")["utilization"].agg(["mean", "std"]).reset_index()

    ax.errorbar(grouped["lambda"], grouped["mean"], yerr=grouped["std"],
                fmt="o-", capsize=4, color="#3498db", linewidth=2, markersize=5,
                label="Simulated S")

    # 理論曲线: S = G * exp(-2G)
    import numpy as np
    g_vals = np.linspace(0.01, df["lambda"].max() * 1.1, 200)
    s_theory = g_vals * np.exp(-2.0 * g_vals)
    ax.plot(g_vals, s_theory, "--", color="#95a5a6", linewidth=1.5,
            label=r"Theoretical $S = G e^{-2G}$")

    ax.set_xlabel("提供的负载G(λ × N × packet_duration)")
    ax.set_ylabel("信道利用率S")
    ax.set_title("纯ALOHA: P–S曲线")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 2. N-S曲线:  标签计数vs信道利用率
# ---------------------------------------------------------------------------
def plot_ns_curve(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制标签数vs.信道利用率。

    参数:
        csv_path: 带有多个(tag_num,利用率)行的CSV的路径。
        out_path: PNG的目标。

    返回:
        保存的图表的路径。
    """
    if out_path is None:
        out_path = os.path.join(
            os.path.dirname(csv_path), "..", "plots", "ns_curve.png"
        )

    df = pd.read_csv(csv_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    grouped = df.groupby("tag_num")["utilization"].agg(["mean", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(grouped["tag_num"], grouped["mean"], yerr=grouped["std"],
                fmt="s-", capsize=4, color="#2ecc71", linewidth=2, markersize=5)
    ax.set_xlabel("标签数N")
    ax.set_ylabel("信道利用率S")
    ax.set_title("纯ALOHA: N–S曲线")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 3. 碰撞率曲线
# ---------------------------------------------------------------------------
def plot_collision_rate(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制碰撞率vs.提供的负载。

    参数:
        csv_path: [lambda,success,collision,利用率]的CSV。
        out_path: 目标PNG。

    返回:
        保存的图表的路径。
    """
    if out_path is None:
        out_path = os.path.join(
            os.path.dirname(csv_path), "..", "plots", "collision_rate.png"
        )

    df = pd.read_csv(csv_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 推导总数据包和碰撞率
    df["total"] = df["success"] + df["collision"]
    df["collision_rate"] = df["collision"] / df["total"]

    grouped = (df.groupby("lambda")["collision_rate"]
               .agg(["mean", "std"]).reset_index())

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(grouped["lambda"], grouped["mean"], yerr=grouped["std"],
                fmt="o-", capsize=4, color="#e74c3c", linewidth=2, markersize=5)
    ax.set_xlabel("提供的负载G")
    ax.set_ylabel("碰撞率")
    ax.set_title("纯ALOHA: 碰撞率")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 4. 时间轴碰撞图表
# ---------------------------------------------------------------------------
def plot_timeline(events_json_path: str,
                  max_packets: int = 80,
                  time_range: Optional[tuple] = None,
                  out_path: Optional[str] = None) -> str:
    """绘制甄特图式时间轴,扩示每个数据包及其碰撞状态。

    参数:
        events_json_path: 原始事件JSON文件的路径。
        max_packets: 要绘制的数据包数的上限(以一会成。
        time_range: 可选(t_min,t_max)缩放窗口。
        out_path: 目标PNG。

    返回:
        保存的图表的路径。
    """
    if out_path is None:
        out_path = os.path.join(
            os.path.dirname(events_json_path), "..", "plots", "timeline.png"
        )

    with open(events_json_path, "r") as fh:
        events = json.load(fh)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 限制数据包数
    if len(events) > max_packets:
        events = events[:max_packets]

    # 确定时间范围
    if time_range is None:
        t_min = min(e["start_time"] for e in events)
        t_max = max(e["end_time"] for e in events)
    else:
        t_min, t_max = time_range
        events = [e for e in events
                  if e["end_time"] > t_min and e["start_time"] < t_max]

    fig, ax = plt.subplots(figsize=(14, max(6, len(events) * 0.15)))

    for idx, evt in enumerate(events):
        start = evt["start_time"]
        end = evt["end_time"]
        collided = evt["collided"]
        partial = evt.get("partial_collision", False)

        if not collided:
            color = SUCCESS_COLOR
        elif partial:
            color = PARTIAL_COLOR
        else:
            color = FULL_COLOR

        ax.barh(idx, end - start, left=start, height=0.7,
                color=color, edgecolor="white", linewidth=0.3)

    ax.set_xlabel("仿真时间(s)")
    ax.set_ylabel("数据包索引")
    ax.set_title("纯ALOHA: 传输时间轴")
    ax.set_xlim(t_min, t_max)
    ax.invert_yaxis()

    # 图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=SUCCESS_COLOR, label="成功"),
        Patch(facecolor=PARTIAL_COLOR, label="部分碰撞"),
        Patch(facecolor=FULL_COLOR, label="完全碰撞"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 批量运行器
# ---------------------------------------------------------------------------
def plot_all(csv_path: str, events_json_path: str,
             plots_dir: str = "results/plots") -> dict:
    """生成所有标准图表。

    返回:
        字典映射图表名称 → 输出文件路径。
    """
    os.makedirs(plots_dir, exist_ok=True)
    results = {}
    results["ps_curve"] = plot_ps_curve(
        csv_path, os.path.join(plots_dir, "ps_curve.png"))
    results["ns_curve"] = plot_ns_curve(
        csv_path, os.path.join(plots_dir, "ns_curve.png"))
    results["collision_rate"] = plot_collision_rate(
        csv_path, os.path.join(plots_dir, "collision_rate.png"))
    results["timeline"] = plot_timeline(
        events_json_path, out_path=os.path.join(plots_dir, "timeline.png"))
    return results
