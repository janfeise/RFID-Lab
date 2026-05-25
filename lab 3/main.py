"""时隙 ALOHA 仿真 - 主入口。

用法:
    python main.py                     # 使用默认配置运行一次仿真
    python main.py --tag-count-sweep    # 对多个标签数运行多次单次仿真并绘制总览图
    python main.py --sweep              # 扫描发送概率和标签数，并生成曲线图
    python main.py --plot               # 根据已有 CSV 重新生成图表
"""

import argparse
import csv
import json
import os
import random

from analysis.plot import plot_all, plot_tag_count_overview
from analysis.report import generate_report
from config import Config
from core.simulator import Simulator


CSV_HEADER = [
    "tag_count",
    "send_probability",
    "slot_size",
    "slot_count",
    "success_count",
    "collision_count",
    "idle_slot_count",
    "total_attempts",
    "throughput",
    "channel_utilization",
    "offered_load",
]


def ensure_dirs(config: Config) -> None:
    """如果输出目录不存在，就创建它们。"""
    for path in [config.results_raw, config.results_csv, config.results_plots]:
        os.makedirs(path, exist_ok=True)


def _save_events(events_path: str, packets) -> None:
    events_data = [packet.to_dict() for packet in packets]
    with open(events_path, "w", encoding="utf-8") as fh:
        json.dump(events_data, fh, indent=2)


def _write_stats_row(writer: csv.writer, stats) -> None:
    writer.writerow([
        stats.tag_count,
        stats.send_probability,
        stats.slot_size,
        stats.slot_count,
        stats.success_count,
        stats.collision_count,
        stats.idle_slot_count,
        stats.total_attempts,
        stats.throughput,
        stats.channel_utilization,
        stats.offered_load,
    ])


def _run_simulation(config: Config):
    random.seed(config.random_seed)
    sim = Simulator(config)
    stats = sim.run()
    return sim, stats


def run_single(config: Config) -> str:
    """运行一次仿真并保存原始事件、CSV 摘要和报告。"""
    ensure_dirs(config)
    print(
        "运行时隙 ALOHA 仿真: "
        f"N={config.tag_count}, P={config.send_probability:.4f}, "
        f"slot={config.slot_size:.4f}s, slots={config.slot_count}, "
        f"T={config.sim_time:.4f}s"
    )

    sim, stats = _run_simulation(config)
    print(stats.summary())

    raw_path = os.path.join(config.results_raw, "events.json")
    _save_events(raw_path, sim.packets)
    print(f"原始事件已保存 → {raw_path}")

    csv_path = os.path.join(config.results_csv, "sim_result.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)
        _write_stats_row(writer, stats)
    print(f"CSV 摘要已保存 → {csv_path}")

    report_path = generate_report(raw_path, stats.summary())
    print(f"报告已保存 → {report_path}")

    return raw_path


def run_sweep(base_config: Config) -> str:
    """扫描发送概率，输出适合绘图的多行 CSV。"""
    ensure_dirs(base_config)

    probability_values = [0.02, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40]

    csv_path = os.path.join(base_config.results_csv, "sweep_results.csv")
    raw_path = os.path.join(base_config.results_raw, "events.json")
    last_events = []

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)

        print("\n" + "=" * 50)
        print("扫描发送概率 P...")
        print("=" * 50)
        for send_probability in probability_values:
            cfg = Config(
                tag_count=base_config.tag_count,
                send_probability=send_probability,
                slot_size=base_config.slot_size,
                slot_count=base_config.slot_count,
                random_seed=base_config.random_seed,
                results_raw=base_config.results_raw,
                results_csv=base_config.results_csv,
                results_plots=base_config.results_plots,
            )
            sim, stats = _run_simulation(cfg)
            _write_stats_row(writer, stats)
            last_events = [packet.to_dict() for packet in sim.packets]
            print(
                f"  P={send_probability:.4f} → S={stats.throughput:.6f} "
                f"(success={stats.success_count}, collision={stats.collision_count}, idle={stats.idle_slot_count})"
            )


    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(last_events, fh, indent=2)

    print(f"\nSweep results saved → {csv_path}")
    print(f"Last run events saved → {raw_path}")
    return csv_path


def _parse_tag_counts(raw_value: str) -> list[int]:
    values = [chunk for chunk in raw_value.replace(",", " ").split() if chunk]
    tag_counts = [int(value) for value in values]
    if not tag_counts:
        raise ValueError("tag_counts 不能为空")
    return tag_counts


def run_tag_count_sweep(base_config: Config, tag_counts: list[int]) -> tuple[str, str]:
    """对多个标签数量分别运行单次仿真，并绘制总览图。"""
    ensure_dirs(base_config)

    csv_path = os.path.join(base_config.results_csv, "tag_count_sweep_results.csv")
    plot_path = os.path.join(base_config.results_plots, "tag_count_overview.png")
    raw_path = os.path.join(base_config.results_raw, "events.json")
    results: list[dict[str, float]] = []
    last_events = []

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)

        print("\n" + "=" * 50)
        print("对标签数量进行多次单次仿真...")
        print("=" * 50)

        for tag_count in tag_counts:
            cfg = Config(
                tag_count=tag_count,
                send_probability=base_config.send_probability,
                slot_size=base_config.slot_size,
                slot_count=base_config.slot_count,
                random_seed=base_config.random_seed,
                results_raw=base_config.results_raw,
                results_csv=base_config.results_csv,
                results_plots=base_config.results_plots,
            )
            sim, stats = _run_simulation(cfg)

            row = {
                "tag_count": float(stats.tag_count),
                "send_probability": float(stats.send_probability),
                "slot_size": float(stats.slot_size),
                "slot_count": float(stats.slot_count),
                "success_count": float(stats.success_count),
                "collision_count": float(stats.collision_count),
                "idle_slot_count": float(stats.idle_slot_count),
                "total_attempts": float(stats.total_attempts),
                "throughput": float(stats.throughput),
                "channel_utilization": float(stats.channel_utilization),
                "offered_load": float(stats.offered_load),
            }
            results.append(row)
            _write_stats_row(writer, stats)
            last_events = [packet.to_dict() for packet in sim.packets]
            print(
                f"  N={tag_count:3d} → S={stats.throughput:.6f} "
                f"(success={stats.success_count}, collision={stats.collision_count}, idle={stats.idle_slot_count})"
            )

    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(last_events, fh, indent=2)

    generated_plot = plot_tag_count_overview(results, plot_path)
    print(f"\nTag-count sweep results saved → {csv_path}")
    print(f"Tag-count overview plot saved → {generated_plot}")
    return csv_path, generated_plot


def _pick_csv_for_plot(config: Config) -> str:
    candidates = [
        os.path.join(config.results_csv, "tag_count_sweep_results.csv"),
        os.path.join(config.results_csv, "sweep_results.csv"),
        os.path.join(config.results_csv, "sim_result.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="时隙 ALOHA 离散时隙仿真器")
    parser.add_argument("--sweep", action="store_true", help="运行发送概率和标签数扫描")
    parser.add_argument("--plot", action="store_true", help="从保存的 CSV 数据生成图表")
    parser.add_argument("--tag-count-sweep", action="store_true", help="对多个标签数量运行单次仿真并绘制总览图")
    parser.add_argument("--tag-counts", type=str, default=None, help="覆盖标签数量列表，例如 10,20,50,100,150,200,300")
    parser.add_argument("--tag-count", type=int, default=None, help="覆盖标签数量")
    parser.add_argument("--send-probability", type=float, default=None, help="覆盖发送概率 P")
    parser.add_argument("--slot-size", type=float, default=None, help="覆盖时隙大小")
    parser.add_argument("--slot-count", type=int, default=None, help="覆盖总时隙数量")
    args = parser.parse_args()

    config = Config()

    if args.tag_count is not None:
        config.tag_count = args.tag_count
    if args.send_probability is not None:
        config.send_probability = args.send_probability
    if args.slot_size is not None:
        config.slot_size = args.slot_size
    if args.slot_count is not None:
        config.slot_count = args.slot_count

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
        events_path = os.path.join(config.results_raw, "events.json")
        if os.path.exists(csv_path):
            print("\n生成图表...")
            results = plot_all(csv_path, events_path, config.results_plots)
            for name, path in results.items():
                print(f"  {name} → {path}")
    elif args.plot:
        csv_path = _pick_csv_for_plot(config)
        events_path = os.path.join(config.results_raw, "events.json")
        if os.path.exists(csv_path):
            print("生成图表...")
            results = plot_all(csv_path, events_path, config.results_plots)
            for name, path in results.items():
                print(f"  {name} → {path}")
        else:
            print("未找到可绘图的 CSV，请先运行一次仿真或扫描。")
    else:
        print("运行单次仿真...")
        run_single(config)


if __name__ == "__main__":
    main()
