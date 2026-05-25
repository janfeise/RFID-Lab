"""纯ALOHA仿真 — 主入口。

用法:
    python main.py              # 使用默认配置的单次运行
    python main.py --sweep      # 参数扫描(发送间隔和N)
    python main.py --plot       # 从保存的CSV生成图表
"""

import argparse
import csv
import json
import os
import random

from config import Config
from core.simulator import Simulator
from analysis.plot import plot_all, plot_tag_count_overview
from analysis.report import generate_report


# ---------------------------------------------------------------------------
# 目录设置
# ---------------------------------------------------------------------------
def ensure_dirs(config: Config) -> None:
    """如果输出目录不存在,则创建它们。"""
    for path in [config.results_raw, config.results_csv, config.results_plots]:
        os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# 单次仿真运行
# ---------------------------------------------------------------------------
def run_single(config: Config) -> str:
    """运行一次仿真并保存原始事件+CSV摘要。

    返回原始事件JSON文件的路径。
    """
    ensure_dirs(config)
    random.seed(config.random_seed)

    print(f"运行纯ALOHA仿真: "
            f"N={config.tag_count}, I={config.send_interval}, "
            f"jitter={config.send_jitter}, T={config.sim_time}s, "
            f"packet={config.packet_duration}s")

    sim = Simulator(config)
    stats = sim.run()

    # 打印摘要
    print(stats.summary())

    # 保存原始事件
    raw_path = os.path.join(config.results_raw, "events.json")
    events_data = [p.to_dict() for p in sim.packets]
    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(events_data, fh, indent=2)
    print(f"原始事件已保存 → {raw_path}")

    # 保存CSV摘要
    csv_path = os.path.join(config.results_csv, "sim_result.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["tag_num", "send_interval", "success", "collision",
                          "utilization", "offered_load"])
        writer.writerow([
            stats.tag_count,
            stats.send_interval,
            stats.success_count,
            stats.collision_count,
            stats.channel_utilization,
            stats.offered_load,
        ])
    print(f"CSV摘要已保存 → {csv_path}")

    # 生成报告
    report_path = generate_report(raw_path, stats.summary())
    print(f"报告已保存 → {report_path}")

    return raw_path


# ---------------------------------------------------------------------------
# 参数扫描
# ---------------------------------------------------------------------------
def run_sweep(base_config: Config) -> str:
    """在发送间隔和N值的范围内运行仿真。

    保存适合绘制P–S和N–S曲线的多行CSV。

    返回扫描CSV的路径。
    """
    ensure_dirs(base_config)

    # 发送间隔扫描(固定N)——从密集发送到稀疏发送
    interval_values = [0.20, 0.30, 0.40, 0.50, 0.60, 0.80,
                       1.00, 1.25, 1.50, 2.00]

    # 标签计数扫描(固定发送间隔)
    n_values = [10, 20, 30, 40, 50, 60, 80, 100, 150, 200]

    csv_path = os.path.join(base_config.results_csv, "sweep_results.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["tag_num", "send_interval", "success", "collision",
                          "utilization", "offered_load"])

        # 对发送间隔进行扫描
        print("\n" + "=" * 50)
        print("对发送间隔进行扫描...")
        print("=" * 50)
        for send_interval in interval_values:
            cfg = Config(
                tag_count=base_config.tag_count,
                send_interval=send_interval,
                send_jitter=base_config.send_jitter,
                sim_time=base_config.sim_time,
                packet_duration=base_config.packet_duration,
                backoff_max=base_config.backoff_max,
                random_seed=base_config.random_seed,
                results_raw=base_config.results_raw,
                results_csv=base_config.results_csv,
                results_plots=base_config.results_plots,
            )
            random.seed(cfg.random_seed)
            sim = Simulator(cfg)
            stats = sim.run()
            writer.writerow([
                stats.tag_count, stats.send_interval,
                stats.success_count, stats.collision_count,
                stats.channel_utilization, stats.offered_load,
            ])
            print(f"  I={send_interval:.4f}  →  S={stats.channel_utilization:.6f}  "
                  f"(success={stats.success_count}, collisions={stats.collision_count})")

        # 对N进行扫描
        print("\n" + "=" * 50)
        print("对N(标签计数)进行扫描...")
        print("=" * 50)
        for n in n_values:
            cfg = Config(
                tag_count=n,
                send_interval=base_config.send_interval,
                send_jitter=base_config.send_jitter,
                sim_time=base_config.sim_time,
                packet_duration=base_config.packet_duration,
                backoff_max=base_config.backoff_max,
                random_seed=base_config.random_seed,
                results_raw=base_config.results_raw,
                results_csv=base_config.results_csv,
                results_plots=base_config.results_plots,
            )
            random.seed(cfg.random_seed)
            sim = Simulator(cfg)
            stats = sim.run()
            writer.writerow([
                stats.tag_count, stats.send_interval,
                stats.success_count, stats.collision_count,
                stats.channel_utilization, stats.offered_load,
            ])
            print(f"  N={n:3d}  →  S={stats.channel_utilization:.6f}  "
                  f"(success={stats.success_count}, collisions={stats.collision_count})")

    print(f"\nSweep results saved → {csv_path}")
    return csv_path


# ---------------------------------------------------------------------------
# 多次单次仿真综合绘图
# ---------------------------------------------------------------------------
def _parse_tag_counts(raw_value: str) -> list[int]:
    values = [chunk for chunk in raw_value.replace(",", " ").split() if chunk]
    tag_counts = [int(value) for value in values]
    if not tag_counts:
        raise ValueError("tag_counts 不能为空")
    return tag_counts


def run_tag_count_sweep(base_config: Config, tag_counts: list[int]) -> tuple[str, str]:
    """对多个标签数量分别运行单次仿真，并绘制综合利用率曲线。"""
    ensure_dirs(base_config)

    csv_path = os.path.join(base_config.results_csv, "tag_count_sweep_results.csv")
    plot_path = os.path.join(base_config.results_plots, "tag_count_overview.png")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    results: list[dict[str, float]] = []

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "tag_count",
            "success_count",
            "collision_count",
            "partial_collision_count",
            "full_collision_count",
            "total_packets",
            "success_rate",
            "channel_utilization",
        ])

        print("\n" + "=" * 50)
        print("对标签数量进行多次单次仿真...")
        print("=" * 50)

        for tag_count in tag_counts:
            cfg = Config(
                tag_count=tag_count,
                send_interval=base_config.send_interval,
                send_jitter=base_config.send_jitter,
                sim_time=base_config.sim_time,
                packet_duration=base_config.packet_duration,
                backoff_max=base_config.backoff_max,
                random_seed=base_config.random_seed,
                results_raw=base_config.results_raw,
                results_csv=base_config.results_csv,
                results_plots=base_config.results_plots,
            )
            random.seed(cfg.random_seed)
            sim = Simulator(cfg)
            stats = sim.run()

            row = {
                "tag_count": float(stats.tag_count),
                "success_count": float(stats.success_count),
                "collision_count": float(stats.collision_count),
                "partial_collision_count": float(stats.partial_collision_count),
                "full_collision_count": float(stats.full_collision_count),
                "total_packets": float(stats.total_packets),
                "success_rate": float(stats.success_rate),
                "channel_utilization": float(stats.channel_utilization),
            }
            results.append(row)
            writer.writerow([
                stats.tag_count,
                stats.success_count,
                stats.collision_count,
                stats.partial_collision_count,
                stats.full_collision_count,
                stats.total_packets,
                stats.success_rate,
                stats.channel_utilization,
            ])
            print(
                f"  N={tag_count:3d}  →  P={stats.success_rate:.6f}, S={stats.channel_utilization:.6f}  "
                f"(success={stats.success_count}, collisions={stats.collision_count})"
            )

    generated_plot = plot_tag_count_overview(results, plot_path)
    print(f"\nTag-count sweep results saved → {csv_path}")
    print(f"Tag-count overview plot saved → {generated_plot}")
    return csv_path, generated_plot


# ---------------------------------------------------------------------------
# 命令行界面
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="纯ALOHA离散事件仿真器"
    )
    parser.add_argument("--sweep", action="store_true",
                        help="运行参数扫描(发送间隔和N)")
    parser.add_argument("--plot", action="store_true",
                        help="从保存的CSV数据生成图表")
    parser.add_argument("--tag-count-sweep", action="store_true",
                        help="对多个标签数量运行单次仿真并绘制综合曲线")
    parser.add_argument("--tag-counts", type=str, default=None,
                        help="覆盖标签数量列表，例如 10,20,50,100,150,200,300")
    parser.add_argument("--tag-count", type=int, default=None,
                        help="覆盖标签数量")
    parser.add_argument("--send-interval", type=float, default=None,
                        help="覆盖基础发送间隔")
    parser.add_argument("--send-jitter", type=float, default=None,
                        help="覆盖发送抖动")
    parser.add_argument("--sim-time", type=float, default=None,
                        help="覆盖仿真时间")
    args = parser.parse_args()

    config = Config()

    # 应用CLI覆盖
    if args.tag_count is not None:
        config.tag_count = args.tag_count
    if args.send_interval is not None:
        config.send_interval = args.send_interval
    if args.send_jitter is not None:
        config.send_jitter = args.send_jitter
    if args.sim_time is not None:
        config.sim_time = args.sim_time

    if args.tag_count_sweep:
        tag_counts = (
            _parse_tag_counts(args.tag_counts)
            if args.tag_counts is not None
            else [10, 15, 20, 25, 30, 40, 50, 75, 100, 125, 150, 200, 250, 300]
        )
        csv_path, plot_path = run_tag_count_sweep(config, tag_counts)
        print(f"  csv → {csv_path}")
        print(f"  plot → {plot_path}")
    elif args.sweep:
        csv_path = run_sweep(config)
        # 扫描后自动生成图表
        events_path = os.path.join(config.results_raw, "events.json")
        if os.path.exists(events_path) and os.path.exists(csv_path):
            print("\n生成图表...")
            results = plot_all(csv_path, events_path, config.results_plots)
            for name, path in results.items():
                print(f"  {name} → {path}")
    elif args.plot:
        csv_path = os.path.join(config.results_csv, "sweep_results.csv")
        events_path = os.path.join(config.results_raw, "events.json")
        if not os.path.exists(csv_path):
            # 回退到单次运行CSV
            csv_path = os.path.join(config.results_csv, "sim_result.csv")
        print("生成图表...")
        results = plot_all(csv_path, events_path, config.results_plots)
        for name, path in results.items():
            print(f"  {name} → {path}")
    else:
        print("运行单次仿真...")
        raw_path = run_single(config)
        # 自动绘图
        # csv_path = os.path.join(config.results_csv, "sim_result.csv")
        # print("\n生成图表...")
        # results = plot_all(csv_path, raw_path, config.results_plots)
        # for name, path in results.items():
        #     print(f"  {name} → {path}")


if __name__ == "__main__":
    main()
