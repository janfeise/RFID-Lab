"""时隙 ALOHA 的全局仿真配置。"""

from dataclasses import dataclass


@dataclass
class Config:
    """时隙 ALOHA 仿真参数。

    除非另有说明，所有时间单位均为秒。
    """

    # --- 标签/发送参数 ---
    tag_count: int = 50             # N: 标签数量
    send_probability: float = 0.03   # P: 每个时隙内的发送概率

    # --- 仿真参数 ---
    slot_size: float = 0.01         # 一个时隙的时长(秒)
    slot_count: int = 10000          # 总时隙数量
    random_seed: int = 45           # PRNG 种子用于可重复性

    # --- 输出目录(相对于项目根目录) ---
    results_raw: str = "results/raw"
    results_csv: str = "results/csv"
    results_plots: str = "results/plots"

    @property
    def sim_time(self) -> float:
        """总仿真时长(秒)。"""
        return self.slot_size * self.slot_count

    @property
    def packet_duration(self) -> float:
        """单个分组占用时长，等于一个时隙长度。"""
        return self.slot_size

    @property
    def packet_duration_ms(self) -> float:
        """单个分组占用时长(毫秒)，用于显示。"""
        return self.packet_duration * 1000.0
