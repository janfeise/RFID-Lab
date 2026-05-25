"""纯ALOHA仿真的数据包模型。"""

from dataclasses import dataclass, field


@dataclass
class Packet:
    """由标签传输的数据包。

    每个数据包占据连续时间间隔[start_time,end_time)。
    碰撞标志由仿真后的碰撞检测器设置。
    """

    tag_id: int
    start_time: float
    duration: float
    end_time: float = field(init=False)

    collided: bool = False
    partial_collision: bool = False
    full_collision: bool = False

    def __post_init__(self) -> None:
        self.end_time = self.start_time + self.duration

    @property
    def is_success(self) -> bool:
        """如果数据包在没有任何碰撞的情况下被传输,则为True。"""
        return not self.collided

    def to_dict(self) -> dict:
        """序列化为普通字典(UTF-8JSON导出)。"""
        return {
            "tag_id": self.tag_id,
            "start_time": round(self.start_time, 6),
            "end_time": round(self.end_time, 6),
            "duration": self.duration,
            "collided": self.collided,
            "partial_collision": self.partial_collision,
            "full_collision": self.full_collision,
        }

    def __repr__(self) -> str:
        status = "成功" if not self.collided else (
            "部分" if self.partial_collision else "完全"
        )
        return (
            f"Packet(tag={self.tag_id}, "
            f"t=[{self.start_time:.4f}, {self.end_time:.4f}], "
            f"{status})"
        )
