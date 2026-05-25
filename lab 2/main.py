"""纯ALOHA仿真 — 主入口。

用法:
    python main.py              # 使用默认配置的单次运行
    python main.py --sweep      # 参数扫描(λ和N)
    python main.py --plot       # 从保存的CSV生成图表
"""

import argparse
import csv
import json
import os
import random
import sys

from config import Config
from core.simulator import Simulator
from analysis.plot import plot_all
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
          f"N={config.tag_count}, λ={config.lam}, "
          f"T={config.sim_time}s, packet={config.packet_duration}s")

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
        writer.writerow(["tag_num", "lambda", "success", "collision",
                          "utilization", "offered_load"])
        writer.writerow([
            stats.tag_count,
            stats.lam,
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
    """在λ和N值的范围内运行仿真。

    保存适合绘制P–S和N–S曲线的多行CSV。

    返回扫描CSV的路径。
    """
    ensure_dirs(base_config)

    # Lambda扫描(固定N)——覆盖G从~0.05到~2.0
    # G = N * λ * T_pkt，所以λ = G / (N * T_pkt)
    n = base_config.tag_count
    t_pkt = base_config.packet_duration
    lam_values = [round(g / (n * t_pkt), 6)
                  for g in [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5,
                            0.6, 0.8, 1.0, 1.2, 1.5, 2.0]]

    # 标签计数扫描(固定λ)
    n_values = [10, 20, 30, 40, 50, 60, 80, 100, 150, 200]

    csv_path = os.path.join(base_config.results_csv, "sweep_results.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["tag_num", "lambda", "success", "collision",
                          "utilization", "offered_load"])

        # 对λ进行扫描
        print("\n" + "=" * 50)
        print("对λ(提供的负载)进行扫描...")
        print("=" * 50)
        for lam in lam_values:
            cfg = Config(
                tag_count=base_config.tag_count,
                lam=lam,
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
                stats.tag_count, stats.lam,
                stats.success_count, stats.collision_count,
                stats.channel_utilization, stats.offered_load,
            ])
            print(f"  λ={lam:.4f}  →  S={stats.channel_utilization:.6f}  "
                  f"(success={stats.success_count}, collisions={stats.collision_count})")

        # 对N进行扫描
        print("\n" + "=" * 50)
        print("对N(标签计数)进行扫描...")
        print("=" * 50)
        for n in n_values:
            cfg = Config(
                tag_count=n,
                lam=base_config.lam,
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
                stats.tag_count, stats.lam,
                stats.success_count, stats.collision_count,
                stats.channel_utilization, stats.offered_load,
            ])
            print(f"  N={n:3d}  →  S={stats.channel_utilization:.6f}  "
                  f"(success={stats.success_count}, collisions={stats.collision_count})")

    print(f"\nSweep results saved → {csv_path}")
    return csv_path


# ---------------------------------------------------------------------------
# 命令行界面
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="纯ALOHA离散事件仿真器"
    )
    parser.add_argument("--sweep", action="store_true",
                        help="运行参数扫描(λ和N)")
    parser.add_argument("--plot", action="store_true",
                        help="从保存的CSV数据生成图表")
    parser.add_argument("--tag-count", type=int, default=None,
                        help="覆盖标签数量")
    parser.add_argument("--lam", type=float, default=None,
                        help="覆盖泊松到达率λ")
    parser.add_argument("--sim-time", type=float, default=None,
                        help="覆盖仿真时间")
    args = parser.parse_args()

    config = Config()

    # 应用CLI覆盖
    if args.tag_count is not None:
        config.tag_count = args.tag_count
    if args.lam is not None:
        config.lam = args.lam
    if args.sim_time is not None:
        config.sim_time = args.sim_time

    if args.sweep:
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
        raw_path = run_single(config)
        # 自动绘图
        csv_path = os.path.join(config.results_csv, "sim_result.csv")
        print("\n生成图表...")
        results = plot_all(csv_path, raw_path, config.results_plots)
        for name, path in results.items():
            print(f"  {name} → {path}")


if __name__ == "__main__":
    main()
