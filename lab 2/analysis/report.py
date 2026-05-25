"""纯ALOHA仿真数据的报告生成。"""

import json
import os
from typing import Optional


def generate_report(events_path: str, stats_summary: str,
                    out_path: Optional[str] = None) -> str:
    """编写markdown报告文件。

    参数:
        events_path: 原始事件JSON的路径。
        stats_summary: Statistics.summary()的预格式化摘要字符串。
        out_path: 报告.md文件的目标。

    返回:
        报告的路径。
    """
    if out_path is None:
        out_path = os.path.join(
            os.path.dirname(events_path), "..", "report.md"
        )

    with open(events_path, "r") as fh:
        events = json.load(fh)

    total = len(events)
    success = sum(1 for e in events if not e["collided"])
    partial = sum(1 for e in events if e.get("partial_collision"))
    full = sum(1 for e in events if e.get("full_collision"))

    lines = [
        "# 纯ALOHA仿真报告",
        "",
        "## 统计",
        "",
        "```",
        stats_summary,
        "```",
        "",
        "## 事件摘要",
        "",
        f"- 总数据包: {total}",
        f"- 成功: {success}",
        f"- 部分碰撞: {partial}",
        f"- 完全碰撞: {full}",
        "",
        "## 图表",
        "",
        "查看`results/plots/`获取图形输出。",
    ]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    content = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return out_path
