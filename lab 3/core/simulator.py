"""时隙 ALOHA 主流程。

流程很直接：按时隙推进 -> 每个 Tag 独立掷硬币 -> 统计成功、碰撞和空闲。
"""

import random
from dataclasses import dataclass, field
from typing import List

from config import Config
from models.packet import Packet


@dataclass
class Tag:
    """标签状态。"""

    tag_id: int
    total_packets_sent: int = 0

    def make_packet(self, slot_index: int, start_time: float,
                    duration: float) -> Packet:
        self.total_packets_sent += 1
        return Packet(
            tag_id=self.tag_id,
            slot_index=slot_index,
            start_time=start_time,
            duration=duration,
        )


@dataclass
class Stats:
    """统计结果。"""

    tag_count: int = 0
    send_probability: float = 0.0
    slot_size: float = 0.0
    slot_count: int = 0

    success_count: int = 0
    collision_count: int = 0
    idle_slot_count: int = 0

    total_attempts: int = 0
    success_time_total: float = 0.0

    _packets: List[Packet] = field(default_factory=list, repr=False)

    def record(self, packets: List[Packet], idle_slot_count: int,
               collision_count: int) -> None:
        self._packets = packets
        self.total_attempts = len(packets)
        self.idle_slot_count = idle_slot_count
        self.collision_count = collision_count
        self.success_count = sum(1 for packet in packets if packet.is_success)
        self.success_time_total = self.success_count * self.slot_size

    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts

    @property
    def collision_rate(self) -> float:
        if self.slot_count == 0:
            return 0.0
        return self.collision_count / self.slot_count

    @property
    def idle_rate(self) -> float:
        if self.slot_count == 0:
            return 0.0
        return self.idle_slot_count / self.slot_count

    @property
    def throughput(self) -> float:
        if self.slot_count == 0:
            return 0.0
        return self.success_count / self.slot_count

    @property
    def channel_utilization(self) -> float:
        if self.slot_count <= 0 or self.slot_size <= 0:
            return 0.0
        return self.success_time_total / (self.slot_count * self.slot_size)

    @property
    def offered_load(self) -> float:
        if self.slot_count <= 0:
            return 0.0
        return self.total_attempts / self.slot_count

    def summary(self) -> str:
        lines = [
            "=" * 50,
            "时隙 ALOHA 仿真摘要",
            "=" * 50,
            f"  标签数:            {self.tag_count}",
            f"  发送概率 P:        {self.send_probability:.4f}",
            f"  时隙大小:          {self.slot_size:.4f} s",
            f"  总时隙数:          {self.slot_count}",
            f"  总仿真时间:        {self.slot_count * self.slot_size:.4f} s",
            f"  总发送尝试:        {self.total_attempts}",
            "-" * 50,
            f"  成功时隙:          {self.success_count} ({self.success_rate:.2%})",
            f"  碰撞时隙:          {self.collision_count} ({self.collision_rate:.2%})",
            f"  空闲时隙:          {self.idle_slot_count} ({self.idle_rate:.2%})",
            "-" * 50,
            f"  提供负载 G:        {self.offered_load:.6f}",
            f"  吞吐量 S:          {self.throughput:.6f}",
            f"  信道利用率 U:      {self.channel_utilization:.6f}",
            "=" * 50,
        ]
        return "\n".join(lines)


class Simulator:
    """时隙 ALOHA 仿真器。

    使用示例:
        cfg = Config(tag_count=50, send_probability=0.2, slot_size=0.01, slot_count=1000)
        sim = Simulator(cfg)
        stats = sim.run()
        print(stats.summary())
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.tags: List[Tag] = []
        self.packets: List[Packet] = []
        self.stats = Stats(
            tag_count=config.tag_count,
            send_probability=config.send_probability,
            slot_size=config.slot_size,
            slot_count=config.slot_count,
        )

    def run(self) -> Stats:
        self._reset()
        self._build_tags()
        self._simulate_slots()
        self._finish()
        return self.stats

    def _reset(self) -> None:
        self.tags = []
        self.packets = []
        self.stats = Stats(
            tag_count=self.config.tag_count,
            send_probability=self.config.send_probability,
            slot_size=self.config.slot_size,
            slot_count=self.config.slot_count,
        )

    def _build_tags(self) -> None:
        self.tags = [
            Tag(tag_id=tag_id)
            for tag_id in range(self.config.tag_count)
        ]

    def _simulate_slots(self) -> None:
        """逐个时隙推进仿真。"""
        cfg = self.config
        for slot_index in range(cfg.slot_count):
            start_time = slot_index * cfg.slot_size

            # 每个 Tag 在当前时隙内独立决定是否发送。
            transmitting_tags = [
                tag for tag in self.tags
                if random.random() < cfg.send_probability
            ]

            if not transmitting_tags:
                self.stats.idle_slot_count += 1
                continue

            if len(transmitting_tags) == 1:
                tag = transmitting_tags[0]
                packet = tag.make_packet(
                    slot_index=slot_index,
                    start_time=start_time,
                    duration=cfg.slot_size,
                )
                self.packets.append(packet)
                self.stats.success_count += 1
                self.stats.total_attempts += 1
                continue

            # 同一时隙里多个 Tag 同时发送，所有分组都失败。
            self.stats.collision_count += 1
            self.stats.total_attempts += len(transmitting_tags)
            for tag in transmitting_tags:
                packet = tag.make_packet(
                    slot_index=slot_index,
                    start_time=start_time,
                    duration=cfg.slot_size,
                )
                packet.collided = True
                self.packets.append(packet)

    def _finish(self) -> None:
        # 仿真结束后，把各项计数汇总到 Stats 中。
        self.stats.record(
            self.packets,
            idle_slot_count=self.stats.idle_slot_count,
            collision_count=self.stats.collision_count,
        )
