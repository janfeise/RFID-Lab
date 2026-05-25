"""纯 ALOHA 仿真结果的绘图和可视化。

生成四个标准图表:
    1. 发送间隔曲线:    发送间隔 vs. 信道利用率
    2. N-S 曲线:        标签计数 vs. 信道利用率
    3. 碰撞率曲线:      发送间隔 vs. 碰撞比率
    4. 时间轴图表:      数据包碰撞视图
"""

import json
import math
import os
from typing import Optional, Sequence

import matplotlib
matplotlib.use("Agg")  # 非互动式后端
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib import patheffects
import pandas as pd


# ---------------------------------------------------------------------------
# 调色板
# ---------------------------------------------------------------------------
SUCCESS_COLOR = "#2ecc71"
PARTIAL_COLOR = "#f39c12"
FULL_COLOR = "#e74c3c"
THEORETICAL_LIMIT = 1 / (2 * math.e)


def _configure_chinese_font() -> None:
    """优先选择系统中可用的中文字体，避免图中文字乱码。"""
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    preferred_fonts = [
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Zen Hei",
        "Arial Unicode MS",
    ]

    for font_name in preferred_fonts:
        if font_name in available_fonts:
            matplotlib.rcParams["font.family"] = [font_name]
            break

    matplotlib.rcParams["axes.unicode_minus"] = False


_configure_chinese_font()


def _interval_col(df: pd.DataFrame) -> str:
    if "send_interval" in df.columns:
        return "send_interval"
    if "lambda" in df.columns:
        return "lambda"
    raise KeyError("CSV 缺少 send_interval 或 lambda 列")


# ---------------------------------------------------------------------------
# 1. 发送间隔曲线:  发送间隔 vs 信道利用率
# ---------------------------------------------------------------------------
def plot_ps_curve(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制发送间隔 vs. 信道利用率。

    参数:
        csv_path: 一个CSV文件的路径,具有列[tag_num,send_interval,success,
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

    # 按发送间隔分组并平均利用率
    interval_col = _interval_col(df)
    grouped = df.groupby(interval_col)["utilization"].agg(["mean", "std"]).reset_index()

    ax.errorbar(grouped[interval_col], grouped["mean"], yerr=grouped["std"],
                fmt="o-", capsize=4, color="#3498db", linewidth=2, markersize=5,
                label="Simulated S")

    ax.set_xlabel("发送间隔(s)")
    ax.set_ylabel("信道利用率S")
    ax.set_title("纯ALOHA: 发送间隔曲线")
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
    """绘制碰撞率vs.发送间隔。

    参数:
        csv_path: [send_interval,success,collision,utilization]的CSV。
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

    interval_col = _interval_col(df)
    grouped = (df.groupby(interval_col)["collision_rate"]
               .agg(["mean", "std"]).reset_index())

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(grouped[interval_col], grouped["mean"], yerr=grouped["std"],
                fmt="o-", capsize=4, color="#e74c3c", linewidth=2, markersize=5)
    ax.set_xlabel("发送间隔(s)")
    ax.set_ylabel("碰撞率")
    ax.set_title("纯ALOHA: 碰撞率")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 4. 多次单次仿真总览图
# ---------------------------------------------------------------------------
def plot_tag_count_overview(results: Sequence[dict[str, float]],
                            out_path: Optional[str] = None) -> str:
    """绘制多次单次仿真的总览图。

    参数:
        results: 形如[{"tag_count": ..., "success_count": ..., "collision_count": ..., ...}, ...]的结果列表。
        out_path: 目标PNG文件路径。

    返回:
        保存的图表路径。
    """
    if not results:
        raise ValueError("results 不能为空")

    if out_path is None:
        out_path = os.path.join(
            "results",
            "plots",
            "tag_count_overview.png",
        )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    df = pd.DataFrame(results)
    required_columns = {"tag_count", "channel_utilization"}
    required_columns.update({"success_count", "collision_count"})
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise KeyError(f"results 缺少必要字段: {missing_text}")

    df = df.sort_values("tag_count")
    if "success_rate" not in df.columns:
        total_packets = df.get("total_packets")
        if total_packets is None:
            total_packets = df["success_count"] + df["collision_count"]
        df["success_rate"] = df["success_count"] / total_packets.replace(0, pd.NA)
        df["success_rate"] = df["success_rate"].fillna(0.0)
    if "partial_collision_count" not in df.columns:
        df["partial_collision_count"] = df["collision_count"]
    if "full_collision_count" not in df.columns:
        df["full_collision_count"] = 0.0

    fig, ax_left = plt.subplots(figsize=(11, 6))
    ax_right = ax_left.twinx()

    x_positions = range(len(df))
    bar_width = 0.34
    success_x = [position - bar_width / 2 for position in x_positions]
    collision_x = [position + bar_width / 2 for position in x_positions]

    success_bars = ax_left.bar(
        success_x,
        df["success_count"],
        width=bar_width,
        color="#3498db",
        label="成功次数",
        alpha=0.9,
    )
    partial_bars = ax_left.bar(
        collision_x,
        df["partial_collision_count"],
        width=bar_width,
        color="#f39c12",
        label="部分冲突",
        alpha=0.9,
    )
    full_bars = ax_left.bar(
        collision_x,
        df["full_collision_count"],
        width=bar_width,
        bottom=df["partial_collision_count"],
        color="#e74c3c",
        label="完全冲突",
        alpha=0.9,
    )

    ax_left.bar_label(success_bars, padding=3, fontsize=9)
    ax_left.bar_label(
        partial_bars,
        labels=[str(int(value)) for value in df["partial_collision_count"]],
        label_type="center",
        fontsize=8,
        color="white",
    )
    ax_left.bar_label(
        full_bars,
        labels=[str(int(value)) for value in df["full_collision_count"]],
        label_type="center",
        fontsize=8,
        color="white",
    )

    utilization_line = ax_right.plot(
        list(x_positions),
        df["channel_utilization"],
        color="#16a085",
        marker="o",
        markersize=6,
        linewidth=2,
        label="信道利用率 S",
    )
    # probability_line = ax_right.plot(
    #     list(x_positions),
    #     df["success_rate"],
    #     color="#8e44ad",
    #     marker="o",
    #     markersize=6,
    #     linewidth=2,
    #     label="成功概率 P",
    # )
    ax_right.scatter(
        list(x_positions),
        df["channel_utilization"],
        color="#16a085",
        s=35,
        zorder=4,
    )
    # ax_right.scatter(
    #     list(x_positions),
    #     df["success_rate"],
    #     color="#8e44ad",
    #     s=35,
    #     zorder=4,
    # )

    for idx, value in enumerate(df["channel_utilization"]):
        ax_right.annotate(
            f"{value:.3f}",
            (idx, value),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#16a085",
            clip_on=False,
            path_effects=[
                patheffects.withStroke(linewidth=3, foreground="white"),
            ],
        )

    # for idx, value in enumerate(df["success_rate"]):
    #     ax_right.annotate(
    #         f"{value:.2%}",
    #         (idx, value),
    #         textcoords="offset points",
    #         xytext=(0, -18),
    #         ha="center",
    #         va="top",
    #         fontsize=9,
    #         color="#8e44ad",
    #         clip_on=False,
    #         path_effects=[
    #             patheffects.withStroke(linewidth=3, foreground="white"),
    #         ],
    #     )

    ax_right.set_ylim(0, max(1.0, float(max(df["success_rate"].max(), df["channel_utilization"].max())) * 1.18))
    ax_left.set_xticks(list(x_positions))
    ax_left.set_xticklabels([str(int(value)) for value in df["tag_count"]])
    ax_left.set_xlabel("标签数量（Tag Count）")
    ax_left.set_ylabel("成功/冲突次数")
    ax_right.set_ylabel("信道利用率 S / 成功概率 P")
    ax_left.set_title("Pure ALOHA: 多次单次仿真结果总览")
    ax_left.grid(True, axis="y", linestyle="--", alpha=0.35)

    handles = [
        Patch(facecolor="#3498db", label="成功次数"),
        Patch(facecolor="#f39c12", label="部分冲突"),
        Patch(facecolor="#e74c3c", label="完全冲突"),
        Line2D([0], [0], color="#16a085", marker="o", linewidth=2, label="信道利用率 S"),
        # Line2D([0], [0], color="#8e44ad", marker="o", linewidth=2, label="成功概率 P"),   
    ]
    ax_left.legend(handles=handles, loc="upper left")

    limit_y = ax_right.get_ylim()[1]
    ax_right.axhline(
        THEORETICAL_LIMIT,
        linestyle="--",
        linewidth=2,
        color="#7f8c8d",
        alpha=0.85,
    )
    ax_right.annotate(
        "Pure ALOHA 18.4%",
        xy=(1.0, THEORETICAL_LIMIT),
        xycoords=("axes fraction", "data"),
        xytext=(-12, 36),
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=10,
        color="#7f8c8d",
        bbox={
            "boxstyle": "round,pad=0.28",
            "facecolor": "white",
            "edgecolor": "#7f8c8d",
            "alpha": 0.92,
        },
        arrowprops={
            "arrowstyle": "->",
            "color": "#7f8c8d",
            "lw": 1.1,
        },
    )

    total_collision_heights = df["partial_collision_count"] + df["full_collision_count"]
    ax_left.set_ylim(0, max(df["success_count"].max(), total_collision_heights.max()) * 1.18)
    ax_right.set_ylim(0, max(1.0, limit_y))

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_tag_count_utilization(results: Sequence[dict[str, float]],
                               out_path: Optional[str] = None) -> str:
    """兼容旧入口：转到总览图。"""
    return plot_tag_count_overview(results, out_path)


# ---------------------------------------------------------------------------
# 5. 时间轴碰撞图表
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
    if os.path.basename(csv_path) == "tag_count_sweep_results.csv":
        df = pd.read_csv(csv_path)
        results["tag_count_utilization"] = plot_tag_count_utilization(
            df[["tag_count", "channel_utilization"]].to_dict("records"),
            os.path.join(plots_dir, "tag_count_utilization.png"),
        )
    results["timeline"] = plot_timeline(
        events_json_path, out_path=os.path.join(plots_dir, "timeline.png"))
    return results
