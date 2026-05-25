"""纯ALOHA的全局仿真配置。"""

from dataclasses import dataclass


@dataclass
class Config:
    """纯ALOHA仿真参数。

    除非另有说明，所有时间单位均为秒。
    """

    # --- 标签/流量参数 ---
    tag_count: int = 300              # N: 标签数量
    lam: float = 0.02               # λ: 泊松到达率(数据包/秒/标签)
                                    #    聚合G = N·λ·T_pkt ≈ 1.0(中位)

    # --- 仿真参数 ---
    sim_time: float = 1000.0        # 总仿真时间(秒)
    packet_duration: float = 1.0    # 一个数据包的传输时间
    backoff_max: float = 3.0        # 最大随机退避窗口(T_pkt的倍数)
    random_seed: int = 42           # PRNG种子用于可重复性

    # --- 输出目录(相对于项目根目录) ---
    results_raw: str = "results/raw"
    results_csv: str = "results/csv"
    results_plots: str = "results/plots"

    @property
    def packet_duration_ms(self) -> float:
        """数据包持续时间(毫秒)(用于显示)。"""
        return self.packet_duration * 1000.0
