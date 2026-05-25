"""时隙 ALOHA 仿真结果的绘图和可视化。

提供三类常用图：
    1. 发送概率曲线：发送概率 P vs. 吞吐量/信道利用率
    2. N-S 曲线：标签数 N vs. 吞吐量/信道利用率
    3. 多次单次仿真总览图：成功/碰撞/空闲时隙 + 吞吐量
    4. 时间轴图：每个发送尝试在时隙上的分布
"""

import json
import math
import os
from typing import Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib import patheffects
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import pandas as pd


SUCCESS_COLOR = "#2ecc71"
COLLISION_COLOR = "#e67e22"
IDLE_COLOR = "#95a5a6"
THROUGHPUT_COLOR = "#16a085"
THEORETICAL_LIMIT = 1 / math.e


def _configure_chinese_font() -> None:
    """优先选择系统中可用的中文字体。"""
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


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _column_or_any(df: pd.DataFrame, candidates: Sequence[str], label: str) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise KeyError(f"CSV 缺少 {label} 列: {', '.join(candidates)}")


def _metric_column(df: pd.DataFrame) -> str:
    return _column_or_any(
        df,
        ["throughput", "channel_utilization", "utilization"],
        "吞吐量/信道利用率",
    )


def _count_column(df: pd.DataFrame, base_name: str) -> str:
    aliases = {
        "tag_count": ["tag_count", "tag_num"],
        "send_probability": ["send_probability", "probability", "p", "send_interval"],
        "success_count": ["success_count", "success"],
        "collision_count": ["collision_count", "collision"],
        "idle_slot_count": ["idle_slot_count", "idle_count"],
        "slot_count": ["slot_count", "total_slots"],
    }
    return _column_or_any(df, aliases[base_name], base_name)


def plot_ps_curve(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制发送概率 vs. 吞吐量/信道利用率曲线。"""
    if out_path is None:
        out_path = os.path.join(os.path.dirname(csv_path), "..", "plots", "ps_curve.png")

    df = pd.read_csv(csv_path)
    _ensure_dir(out_path)

    prob_col = _count_column(df, "send_probability")
    metric_col = _metric_column(df)
    grouped = df.groupby(prob_col)[metric_col].agg(["mean", "std"]).reset_index()
    grouped["std"] = grouped["std"].fillna(0.0)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        grouped[prob_col],
        grouped["mean"],
        yerr=grouped["std"],
        fmt="o-",
        capsize=4,
        color=THROUGHPUT_COLOR,
        linewidth=2,
        markersize=5,
        label="Simulated S",
    )
    ax.set_xlabel("发送概率 P")
    ax.set_ylabel("吞吐量 / 信道利用率")
    ax.set_title("时隙 ALOHA: 发送概率曲线")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_ns_curve(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制标签数量 vs. 吞吐量/信道利用率曲线。"""
    if out_path is None:
        out_path = os.path.join(os.path.dirname(csv_path), "..", "plots", "ns_curve.png")

    df = pd.read_csv(csv_path)
    _ensure_dir(out_path)

    tag_col = _count_column(df, "tag_count")
    metric_col = _metric_column(df)
    grouped = df.groupby(tag_col)[metric_col].agg(["mean", "std"]).reset_index()
    grouped["std"] = grouped["std"].fillna(0.0)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        grouped[tag_col],
        grouped["mean"],
        yerr=grouped["std"],
        fmt="s-",
        capsize=4,
        color=SUCCESS_COLOR,
        linewidth=2,
        markersize=5,
    )
    ax.set_xlabel("标签数 N")
    ax.set_ylabel("吞吐量 / 信道利用率")
    ax.set_title("时隙 ALOHA: N-S 曲线")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_collision_rate(csv_path: str, out_path: Optional[str] = None) -> str:
    """绘制碰撞率曲线。"""
    if out_path is None:
        out_path = os.path.join(os.path.dirname(csv_path), "..", "plots", "collision_rate.png")

    df = pd.read_csv(csv_path)
    _ensure_dir(out_path)

    x_col = _column_or_any(
        df,
        ["send_probability", "probability", "p", "tag_count", "tag_num", "send_interval", "lambda"],
        "横轴",
    )

    if "slot_count" in df.columns:
        df["collision_rate"] = df[_count_column(df, "collision_count")] / df["slot_count"]
    elif "total_slots" in df.columns:
        df["collision_rate"] = df[_count_column(df, "collision_count")] / df["total_slots"]
    else:
        success_col = _count_column(df, "success_count")
        collision_col = _count_column(df, "collision_count")
        if "idle_slot_count" in df.columns or "idle_count" in df.columns:
            idle_col = _count_column(df, "idle_slot_count")
            total = df[success_col] + df[collision_col] + df[idle_col]
        else:
            total = df[success_col] + df[collision_col]
        df["collision_rate"] = df[collision_col] / total.replace(0, pd.NA)
        df["collision_rate"] = df["collision_rate"].fillna(0.0)

    grouped = df.groupby(x_col)["collision_rate"].agg(["mean", "std"]).reset_index()
    grouped["std"] = grouped["std"].fillna(0.0)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        grouped[x_col],
        grouped["mean"],
        yerr=grouped["std"],
        fmt="o-",
        capsize=4,
        color=COLLISION_COLOR,
        linewidth=2,
        markersize=5,
    )
    ax.set_xlabel(x_col.replace("_", " "))
    ax.set_ylabel("碰撞率")
    ax.set_title("时隙 ALOHA: 碰撞率")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_tag_count_overview(results: Sequence[dict[str, float]],
                            out_path: Optional[str] = None) -> str:
    """绘制多次单次仿真的结果总览图。"""
    if not results:
        raise ValueError("results 不能为空")

    if out_path is None:
        out_path = os.path.join("results", "plots", "tag_count_overview.png")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    df = pd.DataFrame(results)

    tag_col = _count_column(df, "tag_count")
    success_col = _count_column(df, "success_count")
    collision_col = _count_column(df, "collision_count")
    slot_col = _count_column(df, "slot_count") if any(col in df.columns for col in ["slot_count", "total_slots"]) else None

    if "idle_slot_count" not in df.columns and "idle_count" not in df.columns:
        if slot_col is not None:
            df["idle_slot_count"] = df[slot_col] - df[success_col] - df[collision_col]
        else:
            df["idle_slot_count"] = 0
    else:
        idle_col = _count_column(df, "idle_slot_count")
        if idle_col != "idle_slot_count":
            df["idle_slot_count"] = df[idle_col]

    if slot_col is not None and slot_col != "slot_count":
        df["slot_count"] = df[slot_col]
    elif "slot_count" not in df.columns:
        df["slot_count"] = df[success_col] + df[collision_col] + df["idle_slot_count"]

    if "throughput" not in df.columns:
        df["throughput"] = df[success_col] / df["slot_count"].replace(0, pd.NA)
        df["throughput"] = df["throughput"].fillna(0.0)
    if "channel_utilization" not in df.columns:
        df["channel_utilization"] = df["throughput"]

    df = df.sort_values(tag_col)

    fig, ax_left = plt.subplots(figsize=(11, 6))
    ax_right = ax_left.twinx()

    x_positions = list(range(len(df)))
    bar_width = 0.58

    idle_bars = ax_left.bar(
        x_positions,
        df["idle_slot_count"],
        width=bar_width,
        color=IDLE_COLOR,
        label="空闲时隙",
        alpha=0.9,
    )
    collision_bars = ax_left.bar(
        x_positions,
        df[collision_col],
        width=bar_width,
        bottom=df["idle_slot_count"],
        color=COLLISION_COLOR,
        label="碰撞时隙",
        alpha=0.9,
    )
    success_bars = ax_left.bar(
        x_positions,
        df[success_col],
        width=bar_width,
        bottom=df["idle_slot_count"] + df[collision_col],
        color=SUCCESS_COLOR,
        label="成功时隙",
        alpha=0.9,
    )

    ax_left.bar_label(idle_bars, labels=[str(int(value)) for value in df["idle_slot_count"]], label_type="center", fontsize=8, color="white")
    ax_left.bar_label(collision_bars, labels=[str(int(value)) for value in df[collision_col]], label_type="center", fontsize=8, color="white")
    ax_left.bar_label(success_bars, padding=3, fontsize=9)

    ax_right.plot(
        x_positions,
        df["throughput"],
        color=THROUGHPUT_COLOR,
        marker="o",
        markersize=6,
        linewidth=2,
        label="吞吐量 S / 信道利用率 U",
    )
    ax_right.scatter(x_positions, df["throughput"], color=THROUGHPUT_COLOR, s=35, zorder=4)

    for idx, value in enumerate(df["throughput"]):
        ax_right.annotate(
            f"{value:.3f}",
            (idx, value),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            va="bottom",
            fontsize=9,
            color=THROUGHPUT_COLOR,
            clip_on=False,
            path_effects=[patheffects.withStroke(linewidth=3, foreground="white")],
        )

    ax_right.axhline(THEORETICAL_LIMIT, linestyle="--", linewidth=2, color="#7f8c8d", alpha=0.85)
    ax_right.annotate(
        "Slotted ALOHA 1/e ≈ 36.8%",
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

    total_heights = df["idle_slot_count"] + df[collision_col] + df[success_col]
    ax_left.set_ylim(0, max(1.0, float(total_heights.max()) * 1.18))
    ax_right.set_ylim(0, max(1.0, float(max(df["throughput"].max(), THEORETICAL_LIMIT)) * 1.18))

    ax_left.set_xticks(x_positions)
    ax_left.set_xticklabels([str(int(value)) for value in df[tag_col]])
    ax_left.set_xlabel("标签数量 N")
    ax_left.set_ylabel("时隙数量")
    ax_right.set_ylabel("吞吐量 S / 信道利用率 U")
    ax_left.set_title("时隙 ALOHA: 多次单次仿真结果总览")
    ax_left.grid(True, axis="y", linestyle="--", alpha=0.35)

    handles = [
        Patch(facecolor=SUCCESS_COLOR, label="成功时隙"),
        Patch(facecolor=COLLISION_COLOR, label="碰撞时隙"),
        Patch(facecolor=IDLE_COLOR, label="空闲时隙"),
        Line2D([0], [0], color=THROUGHPUT_COLOR, marker="o", linewidth=2, label="吞吐量 S / 信道利用率 U"),
    ]
    ax_left.legend(handles=handles, loc="upper left")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_tag_count_utilization(results: Sequence[dict[str, float]],
                               out_path: Optional[str] = None) -> str:
    """兼容旧入口：转到总览图。"""
    return plot_tag_count_overview(results, out_path)


def plot_timeline(events_json_path: str,
                  max_packets: int = 120,
                  time_range: Optional[tuple] = None,
                  out_path: Optional[str] = None) -> str:
    """绘制时隙发送时间轴。"""
    if out_path is None:
        out_path = os.path.join(os.path.dirname(events_json_path), "..", "plots", "timeline.png")

    with open(events_json_path, "r", encoding="utf-8") as fh:
        events = json.load(fh)

    _ensure_dir(out_path)

    if len(events) > max_packets:
        events = events[:max_packets]

    if not events:
        raise ValueError("events 不能为空")

    if time_range is None:
        t_min = min(e["start_time"] for e in events)
        t_max = max(e["end_time"] for e in events)
    else:
        t_min, t_max = time_range
        events = [e for e in events if e["end_time"] > t_min and e["start_time"] < t_max]

    fig, ax = plt.subplots(figsize=(14, max(6, len(events) * 0.15)))

    for idx, evt in enumerate(events):
        start = evt["start_time"]
        end = evt["end_time"]
        collided = evt.get("collided", False)
        success = evt.get("success", not collided)
        color = SUCCESS_COLOR if success else COLLISION_COLOR

        ax.barh(idx, end - start, left=start, height=0.7, color=color, edgecolor="white", linewidth=0.3)

    ax.set_xlabel("仿真时间(s)")
    ax.set_ylabel("数据包索引")
    ax.set_title("时隙 ALOHA: 发送时间轴")
    ax.set_xlim(t_min, t_max)
    ax.invert_yaxis()

    legend_elements = [
        Patch(facecolor=SUCCESS_COLOR, label="成功"),
        Patch(facecolor=COLLISION_COLOR, label="碰撞"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_all(csv_path: str, events_json_path: str,
             plots_dir: str = "results/plots") -> dict:
    """生成常用图表。"""
    os.makedirs(plots_dir, exist_ok=True)
    results = {}

    results["ps_curve"] = plot_ps_curve(csv_path, os.path.join(plots_dir, "ps_curve.png"))
    results["ns_curve"] = plot_ns_curve(csv_path, os.path.join(plots_dir, "ns_curve.png"))
    results["collision_rate"] = plot_collision_rate(csv_path, os.path.join(plots_dir, "collision_rate.png"))

    df = pd.read_csv(csv_path)
    if any(column in df.columns for column in ["tag_count", "tag_num"]):
        tag_col = "tag_count" if "tag_count" in df.columns else "tag_num"
        if csv_path.endswith("tag_count_sweep_results.csv") or df[tag_col].nunique() > 1:
            results["overview"] = plot_tag_count_overview(
                df.to_dict("records"),
                os.path.join(plots_dir, "tag_count_overview.png"),
            )

    if os.path.exists(events_json_path):
        results["timeline"] = plot_timeline(
            events_json_path,
            out_path=os.path.join(plots_dir, "timeline.png"),
        )

    return results
