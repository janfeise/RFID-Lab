# Pure ALOHA Discrete-Event Simulator

纯 ALOHA 介质访问协议的连续时间、事件驱动仿真

## 架构

```
pure_aloha/
├── main.py                 # 程序入口（单次运行 / 参数扫描 / 绘图）
├── config.py               # 全局参数（数据类）
├── core/
│   └── simulator.py        # 纯 ALOHA 主引擎：事件推进 / 发送 / 碰撞 / 重传 / 统计
├── models/
│   └── packet.py           # 数据包（含碰撞标志）
├── analysis/
│   ├── plot.py             # matplotlib/pandas 可视化
│   └── report.py           # Markdown 报告生成器
├── results/
│   ├── raw/                # events.json — 每个数据包的时间线
│   ├── csv/                # sim_result.csv / sweep_results.csv
│   └── plots/              # PNG 图片
└── README.md
```

## 关键设计决策

### 主流程收敛

Pure ALOHA 的核心执行链现在集中在 `core/simulator.py` 中，按“事件调度 -> 发送开始 -> 发送结束 -> 碰撞判定 -> 重传调度 -> 统计汇总”的顺序组织，便于直接阅读协议机制。

### 连续时间、事件驱动（非时隙）

纯 ALOHA 与时隙 ALOHA 的本质区别在于：标签可以在**任意实数时间点**发送数据，而非离散的时隙边界。

- `heapq` 优先队列按时间顺序调度事件
- 发送间隔遵循**指数（泊松）分布**
- **没有** `for t in range(...)`，没有时隙数组，没有每时隙发送概率

### 碰撞检测

两个数据包的时间区间重叠即发生碰撞：

```
p1.start_time < p2.end_time  AND  p2.start_time < p1.end_time
```

对每个数据包计算所有重叠区间的并集，以区分**部分碰撞**和**完全碰撞**。

### 信道利用率

```
S = T_success / T_total      （理论最大值：1/(2e) ≈ 0.184）
```

## 快速开始

```bash
# 使用默认参数进行单次仿真
python main.py

# 参数扫描（λ 和 N 曲线）
python main.py --sweep

# 根据已有 CSV 数据生成图表
python main.py --plot

# 自定义参数
python main.py --tag-count 100 --lam 0.01 --sim-time 5000
```

## 配置

编辑 `config.py` 或通过命令行参数传递：

| 参数              | 默认值 | 描述                               |
| ----------------- | ------ | ---------------------------------- |
| `tag_count`       | 500    | 标签数量（N）                      |
| `lam`             | 0.02   | 每个标签的泊松到达率 λ             |
| `sim_time`        | 1000.0 | 仿真时长（秒）                     |
| `packet_duration` | 1.0    | 每个数据包的传输时间               |
| `backoff_max`     | 3.0    | 最大随机退避窗口                   |
| `random_seed`     | 42     | 伪随机数生成器种子（用于可重现性） |

总负载：**G = N × λ × packet_duration**

## 输出文件

- `results/raw/events.json` — 每个数据包的时间区间和碰撞状态
- `results/csv/sim_result.csv` — 单次仿真汇总
- `results/csv/sweep_results.csv` — 多轮扫描数据，用于绘制曲线
- `results/plots/ps_curve.png` — 总负载 vs. 信道利用率
- `results/plots/ns_curve.png` — 标签数量 vs. 信道利用率
- `results/plots/collision_rate.png` — 碰撞率 vs. 总负载
- `results/plots/timeline.png` — 甘特图风格的数据包时间线视图

## 扩展说明

模块边界现在更少，主线更集中：

- **时隙 ALOHA**：在 `core/simulator.py` 中引入时隙边界和时隙对齐
- **CSMA**：在 `core/simulator.py` 中添加载波侦听逻辑
- **CSMA/CD**：在 `core/simulator.py` 中扩展传输过程中的碰撞处理
