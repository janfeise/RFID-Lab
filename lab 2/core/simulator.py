"""纯 ALOHA 主流程。

流程：标签初始化 -> 投首包 -> 跑事件 -> 判碰撞 -> 记统计。
"""

import heapq
import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, List

from config import Config
from models.packet import Packet


EventCallback = Callable[..., None]


@dataclass
class Tag:
    """标签运行状态。"""

    tag_id: int
    lam: float
    packet_duration: float
    backoff_max: float
    retry_count: int = 0
    total_packets_sent: int = 0
    next_send_time: float = 0.0

    def make_packet(self, start_time: float) -> Packet:
        self.total_packets_sent += 1
        return Packet(
            tag_id=self.tag_id,
            start_time=start_time,
            duration=self.packet_duration,
        )

    def next_tx(self, current_time: float, collided: bool) -> float:
        if collided:
            self.retry_count += 1
            current_time += random.uniform(0.0, self.backoff_max)
        else:
            self.retry_count = 0

        self.next_send_time = current_time + _exponential_interval(self.lam)
        return self.next_send_time


@dataclass
class Stats:
    """统计结果。"""

    tag_count: int = 0
    lam: float = 0.0
    sim_time: float = 0.0
    packet_duration: float = 0.0

    success_count: int = 0
    collision_count: int = 0
    partial_collision_count: int = 0
    full_collision_count: int = 0

    total_packets: int = 0
    success_time_total: float = 0.0

    _packets: List[Packet] = field(default_factory=list, repr=False)

    def record(self, packets: List[Packet]) -> None:
        self._packets = packets
        self.total_packets = len(packets)
        self.success_count = sum(1 for packet in packets if packet.is_success)
        self.partial_collision_count = sum(
            1 for packet in packets if packet.partial_collision
        )
        self.full_collision_count = sum(
            1 for packet in packets if packet.full_collision
        )
        self.collision_count = (
            self.partial_collision_count + self.full_collision_count
        )
        self.success_time_total = sum(
            packet.duration for packet in packets if packet.is_success
        )

    @property
    def success_rate(self) -> float:
        if self.total_packets == 0:
            return 0.0
        return self.success_count / self.total_packets

    @property
    def collision_rate(self) -> float:
        if self.total_packets == 0:
            return 0.0
        return self.collision_count / self.total_packets

    @property
    def channel_utilization(self) -> float:
        if self.sim_time <= 0:
            return 0.0
        return self.success_time_total / self.sim_time

    @property
    def offered_load(self) -> float:
        if self.sim_time <= 0:
            return 0.0
        return (self.total_packets * self.packet_duration) / self.sim_time

    def summary(self) -> str:
        lines = [
            "=" * 50,
            "纯 ALOHA 仿真摘要",
            "=" * 50,
            f"  标签数:            {self.tag_count}",
            f"  Lambda (λ):        {self.lam:.4f}",
            f"  仿真时间:          {self.sim_time:.2f} s",
            f"  数据包持续时间:    {self.packet_duration:.4f} s",
            f"  总数据包:          {self.total_packets}",
            "-" * 50,
            f"  成功:              {self.success_count} ({self.success_rate:.2%})",
            f"  碰撞:              {self.collision_count} ({self.collision_rate:.2%})",
            f"    部分碰撞:        {self.partial_collision_count}",
            f"    完全碰撞:        {self.full_collision_count}",
            "-" * 50,
            f"  提供的负载 G:      {self.offered_load:.6f}",
            f"  信道利用率 S:      {self.channel_utilization:.6f}",
            f"  理论上限 1/(2e):   {1.0 / (2.0 * math.e):.6f}",
            "=" * 50,
        ]
        return "\n".join(lines)


class Queue:
    """事件队列。"""

    def __init__(self) -> None:
        self._heap: list[list[Any]] = []
        self._seq = 0
        self._current_time = 0.0

    @property
    def current_time(self) -> float:
        return self._current_time

    def schedule(self, time: float, callback: EventCallback, *args: Any,
                 **kwargs: Any) -> None:
        heapq.heappush(
            self._heap,
            [time, self._seq, callback, args, kwargs],
        )
        self._seq += 1

    def run(self, until: float) -> None:
        while self._heap:
            time, _seq, callback, args, kwargs = self._heap[0]
            if time > until:
                break
            heapq.heappop(self._heap)
            self._current_time = time
            callback(*args, **kwargs)

    def clear(self) -> None:
        self._heap.clear()
        self._seq = 0
        self._current_time = 0.0


class Simulator:
    """纯 ALOHA 仿真器。

    使用示例:
        cfg = Config(tag_count=50, lam=0.5, sim_time=1000)
        sim = Simulator(cfg)
        stats = sim.run()
        print(stats.summary())
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.scheduler = Queue()
        self.tags: List[Tag] = []
        self.packets: List[Packet] = []
        self.stats = Stats(
            tag_count=config.tag_count,
            lam=config.lam,
            sim_time=config.sim_time,
            packet_duration=config.packet_duration,
        )

    def run(self) -> Stats:
        self._reset()
        self._build_tags()
        self._seed()
        self.scheduler.run(until=self.config.sim_time)
        self._finish()
        return self.stats

    def _reset(self) -> None:
        self.scheduler.clear()
        self.tags = []
        self.packets = []
        self.stats = Stats(
            tag_count=self.config.tag_count,
            lam=self.config.lam,
            sim_time=self.config.sim_time,
            packet_duration=self.config.packet_duration,
        )

    def _build_tags(self) -> None:
        cfg = self.config
        self.tags = [
            Tag(
                tag_id=tag_id,
                lam=cfg.lam,
                packet_duration=cfg.packet_duration,
                backoff_max=cfg.backoff_max,
            )
            for tag_id in range(cfg.tag_count)
        ]

    def _seed(self) -> None:
        # 每个标签先投一个首包。
        for tag in self.tags:
            self.scheduler.schedule(
                _exponential_interval(tag.lam),
                self._start,
                tag,
            )

    def _start(self, tag: Tag) -> None:
        # 记录发送开始，并安排结束事件。
        current_time = self.scheduler.current_time
        packet = tag.make_packet(current_time)
        self.packets.append(packet)

        end_time = current_time + self.config.packet_duration
        self.scheduler.schedule(end_time, self._end, tag, packet)

    def _end(self, tag: Tag, packet: Packet) -> None:
        # 发送结束后，先看是否碰撞，再决定下一次发送时间。
        collided = any(
            _overlaps(packet, other)
            for other in self.packets
            if other is not packet
        )
        next_time = tag.next_tx(self.scheduler.current_time, collided)
        self.scheduler.schedule(next_time, self._start, tag)

    def _finish(self) -> None:
        # 仿真结束后统一标记碰撞并汇总统计。
        _classify_packets(self.packets)
        self.stats.record(self.packets)


def _exponential_interval(lam: float) -> float:
    return -math.log(1.0 - random.random()) / lam


def _overlaps(p1: Packet, p2: Packet) -> bool:
    return p1.start_time < p2.end_time and p2.start_time < p1.end_time


def _classify_packets(packets: List[Packet]) -> None:
    # 逐包合并重叠区间，区分部分碰撞和完全碰撞。
    for index, packet in enumerate(packets):
        overlap_intervals: List[tuple[float, float]] = []
        for other_index, other in enumerate(packets):
            if index == other_index:
                continue
            if _overlaps(packet, other):
                packet.collided = True
                overlap_start = max(packet.start_time, other.start_time)
                overlap_end = min(packet.end_time, other.end_time)
                overlap_intervals.append((overlap_start, overlap_end))

        if packet.collided:
            if _union_duration(overlap_intervals) >= packet.duration:
                packet.full_collision = True
            else:
                packet.partial_collision = True


def _union_duration(intervals: List[tuple[float, float]]) -> float:
    if not intervals:
        return 0.0

    intervals.sort(key=lambda interval: interval[0])
    total = 0.0
    cur_start, cur_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = start, end

    return total + (cur_end - cur_start)
