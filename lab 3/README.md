# Slotted ALOHA Discrete-Time Simulator

时隙 ALOHA 介质访问协议的离散时隙仿真

## 架构

```
pure_aloha/
├── main.py                 # 程序入口（单次运行 / 参数扫描 / 绘图）
├── config.py               # 全局参数（数据类）
├── core/
│   └── simulator.py        # 时隙 ALOHA 主引擎：逐时隙发送决策 / 统计
├── models/
│   └── packet.py           # 数据包（含碰撞标志）
├── analysis/
│   ├── plot.py             # matplotlib/pandas 可视化
│   └── report.py           # Markdown 报告生成器
├── results/
│   ├── raw/                # events.json — 每个发送尝试的时隙时间线
│   ├── csv/                # sim_result.csv / sweep_results.csv / tag_count_sweep_results.csv
│   └── plots/              # PNG 图片
└── README.md
```

## 关键设计决策

### 主流程收敛

Slotted ALOHA 的核心执行链现在集中在 `core/simulator.py` 中，按“逐时隙推进 -> 每个 Tag 独立掷概率 -> 统计成功 / 碰撞 / 空闲”的顺序组织，便于直接阅读协议机制。

### 简单发送

为了更适合教学演示，每个标签在每个时隙内独立以概率 P 决定是否发送。这样更容易观察“随机发送、同槽竞争、碰撞产生、空闲时隙”的完整流程。

### 离散时隙模型

时隙 ALOHA 的本质区别在于：发送决策只在**时隙边界**上进行。

- `for slot in range(...)` 逐个时隙推进
- 每个 Tag 在每个时隙内独立掷概率
- 若某时隙中只有 1 个 Tag 发送，则成功
- 若某时隙中有多个 Tag 同时发送，则碰撞
- 若某时隙中没有任何 Tag 发送，则为空闲时隙

### 碰撞检测

同一时隙内多个数据包同时发送即发生碰撞：

所有发送者都失败，没有部分碰撞与完全碰撞之分。

### 信道利用率

```
U = T_success / T_total
```

在这个离散模型里，吞吐量 S 和信道利用率 U 数值相同，都是成功时隙占总时隙的比例。

## 快速开始

```bash
# 使用默认参数进行单次仿真
python main.py

# 参数扫描（发送概率 P 曲线）
python main.py --sweep

# 多次单次仿真总览图（标签数量、成功 / 碰撞 / 空闲时隙）
python main.py --tag-count-sweep

# 根据已有 CSV 数据生成图表
python main.py --plot

# 自定义参数
python main.py --tag-count 10 --send-probability 0.2 --slot-size 0.01 --slot-count 1000
```

## 配置

编辑 `config.py` 或通过命令行参数传递：

| 参数               | 默认值 | 描述                               |
| ------------------ | ------ | ---------------------------------- |
| `tag_count`        | 50     | 标签数量（N）                      |
| `send_probability` | 0.2    | 每个时隙内 Tag 发送的概率 P        |
| `slot_size`        | 0.01   | 时隙大小（秒）                     |
| `slot_count`       | 1000   | 总时隙数量                         |
| `random_seed`      | 45     | 伪随机数生成器种子（用于可重现性） |

发送概率越高，碰撞通常越频繁，空闲时隙越少；过高的发送概率也会让吞吐量下降。

## 输出文件

- `results/raw/events.json` — 每个发送尝试的时隙时间区间和碰撞状态
- `results/csv/sim_result.csv` — 单次仿真汇总
- `results/csv/sweep_results.csv` — 发送概率和标签数扫描数据
- `results/csv/tag_count_sweep_results.csv` — 标签数量扫描数据
- `results/plots/ps_curve.png` — 发送概率 vs. 吞吐量 / 信道利用率
- `results/plots/ns_curve.png` — 标签数量 vs. 吞吐量 / 信道利用率
- `results/plots/collision_rate.png` — 碰撞率图
- `results/plots/tag_count_overview.png` — 多次单次仿真总览图
- `results/plots/timeline.png` — 时隙发送时间轴视图

## 扩展说明

模块边界现在更少，主线更集中：

- **纯 ALOHA**：可以保留为另一个实验目录的参考实现
- **CSMA**：在 `core/simulator.py` 中添加载波侦听逻辑
- **CSMA/CD**：在 `core/simulator.py` 中扩展传输过程中的碰撞处理
