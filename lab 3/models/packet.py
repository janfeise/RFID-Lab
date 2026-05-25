"""时隙 ALOHA 仿真的数据包模型。"""

from dataclasses import dataclass, field


@dataclass
class Packet:
    """由标签在某个时隙内发出的数据包。

    在时隙 ALOHA 中，每个分组都严格占用一个时隙长度。
    """

    tag_id: int
    slot_index: int
    start_time: float
    duration: float
    end_time: float = field(init=False)

    collided: bool = False

    def __post_init__(self) -> None:
        self.end_time = self.start_time + self.duration

    @property
    def is_success(self) -> bool:
        """如果数据包成功发送,则返回 True。"""
        return not self.collided

    def to_dict(self) -> dict:
        """序列化为普通字典(UTF-8 JSON 导出)。"""
        return {
            "tag_id": self.tag_id,
            "slot_index": self.slot_index,
            "start_time": round(self.start_time, 6),
            "end_time": round(self.end_time, 6),
            "duration": self.duration,
            "collided": self.collided,
            "success": self.is_success,
        }

    def __repr__(self) -> str:
        status = "成功" if not self.collided else "碰撞"
        return (
            f"Packet(tag={self.tag_id}, slot={self.slot_index}, "
            f"t=[{self.start_time:.4f}, {self.end_time:.4f}], "
            f"{status})"
        )
