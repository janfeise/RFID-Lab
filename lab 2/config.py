"""纯ALOHA的全局仿真配置。"""

from dataclasses import dataclass


@dataclass
class Config:
    """纯ALOHA仿真参数。

    除非另有说明，所有时间单位均为秒。
    """

    # --- 标签/发送参数 ---
    tag_count: int = 50              # N: 标签数量
    send_interval: float = 10.0        # 每次发送之间的基础间隔(秒)
    send_jitter: float = 0.1         # 简单随机抖动(秒)

    # --- 仿真参数 ---
    sim_time: float = 1000.0        # 总仿真时间(秒)
    packet_duration: float = 0.05    # 一个数据包的传输时间
    backoff_max: float = 0.5        # 最大随机退避窗口(T_pkt的倍数)
    random_seed: int = 45           # PRNG种子用于可重复性

    # --- 输出目录(相对于项目根目录) ---
    results_raw: str = "results/raw"
    results_csv: str = "results/csv"
    results_plots: str = "results/plots"

    @property
    def packet_duration_ms(self) -> float:
        """数据包持续时间(毫秒)(用于显示)。"""
        return self.packet_duration * 1000.0
