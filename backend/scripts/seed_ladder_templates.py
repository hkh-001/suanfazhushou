from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.ladder import LadderTemplate, LearningPathNode


def _practice_items(key: str, title: str) -> list[dict]:
    return [
        {
            "id": f"{key}-choice-1",
            "type": "choice",
            "prompt": f"使用「{title}」解题前，最先应该确认什么？",
            "options": [
                {"id": "a", "text": "算法复杂度是否匹配输入规模"},
                {"id": "b", "text": "变量名是否足够短"},
                {"id": "c", "text": "代码是否使用了最新语法"},
            ],
            "correct_option_id": "a",
            "explanation": "算法练习首先要确认思路能否在题目给定的数据范围内完成。",
        },
        {
            "id": f"{key}-choice-2",
            "type": "choice",
            "prompt": "哪种习惯最有助于避免边界错误？",
            "options": [
                {"id": "a", "text": "跳过样例，直接写代码"},
                {"id": "b", "text": "手算一个小例子，并标出下标或状态变化"},
                {"id": "c", "text": "只测试最大规模数据"},
            ],
            "correct_option_id": "b",
            "explanation": "手算小例子能尽早暴露下标越界、少算一项或状态更新顺序错误。",
        },
        {
            "id": f"{key}-coding-1",
            "type": "coding",
            "prompt": f"写一个使用「{title}」的小实现或伪代码片段。",
            "self_check": "确认你测试了最小规模、普通规模和边界规模三类情况。",
        },
    ]


def _node(
    key: str,
    title: str,
    summary: str,
    material: str,
    *,
    topic_slug: str | None = None,
) -> dict:
    node = {
        "algorithm_key": key,
        "title": title,
        "summary": summary,
        "material_markdown": material,
        "resource_links": [],
        "practice_items": _practice_items(key, title),
    }
    if topic_slug:
        node["topic_slug"] = topic_slug
    return node


def _template_data(*, focus: str) -> dict:
    return {
        "phases": [
            {
                "title": "基础阶段",
                "description": "建立算法学习所需的基本概念和解题习惯。",
                "nodes": [
                    _node(
                        "time-complexity",
                        "时间复杂度",
                        "学习在写代码前估算程序运行规模。",
                        (
                            "# 时间复杂度\n\n"
                            "时间复杂度用来描述操作次数随输入规模增长的速度。入门阶段先区分常数、线性、"
                            "对数、平方等常见增长方式。解题时先写下题目的最大数据范围，再选择能在限制内完成的算法。\n\n"
                            "## 检查清单\n\n"
                            "- 找出主要循环或递归。\n"
                            "- 估算每个元素会被处理多少次。\n"
                            "- 将复杂度和输入上限进行比较。\n"
                        ),
                        topic_slug="time-complexity",
                    ),
                    _node(
                        "array-and-string-basics",
                        "数组与字符串基础",
                        "练习下标、边界和简单扫描。",
                        (
                            "# 数组与字符串基础\n\n"
                            "大多数入门算法题都建立在数组和字符串之上。学习重点是下标范围、边界条件、"
                            "以及扫描过程中是否需要维护当前和、最大值或频次数组等状态。\n\n"
                            "## 练习习惯\n\n"
                            "写代码前先构造一个小例子，并标出每一步会访问的下标。"
                        ),
                        topic_slug="array-basics",
                    ),
                ],
            },
            {
                "title": focus,
                "description": "从基础工具过渡到常见算法题型。",
                "nodes": [
                    _node(
                        "sorting",
                        "排序",
                        "利用有序性简化选择、统计和配对问题。",
                        (
                            "# 排序\n\n"
                            "排序会把无序数据变成更容易分析的结构。排序后，相邻元素经常能揭示重复、间隔、"
                            "最优配对或贪心选择。\n\n"
                            "## 常见思考\n\n"
                            "- 排序是否会改变题目的答案？\n"
                            "- 有序之后是否能看出显然的贪心选择？\n"
                            "- `O(n log n)` 是否能通过当前数据范围？"
                        ),
                        topic_slug="sorting",
                    ),
                    _node(
                        "two-pointers",
                        "双指针",
                        "用两个移动下标替代部分嵌套循环。",
                        (
                            "# 双指针\n\n"
                            "双指针通过让下标单调移动来减少重复工作，常用于有序数组、区间、窗口条件等场景。\n\n"
                            "## 核心想法\n\n"
                            "尽量保证每个指针只向一个方向移动。如果指针频繁回退，算法通常就不再是线性的。"
                        ),
                        topic_slug="two-pointers",
                    ),
                ],
            },
        ]
    }


DEFAULT_TEMPLATES = [
    {
        "goal_track": "self_study",
        "current_level": "beginner",
        "name": "自学入门路径",
        "description": "适合独立打基础的紧凑算法路径。",
        "template_data": _template_data(focus="核心题型"),
    },
    {
        "goal_track": "course",
        "current_level": "beginner",
        "name": "课程基础提升路径",
        "description": "面向高级语言程序设计等课程的基础巩固路径。",
        "template_data": _template_data(focus="课程练习"),
    },
    {
        "goal_track": "lanqiao",
        "current_level": "elementary",
        "name": "蓝桥杯入门路径",
        "description": "面向蓝桥杯常见基础题型的准备路径。",
        "template_data": _template_data(focus="蓝桥杯题型"),
    },
    {
        "goal_track": "icpc",
        "current_level": "popularization",
        "name": "ICPC 普及进阶路径",
        "description": "从基础竞赛题型过渡到 ICPC 训练的路径。",
        "template_data": _template_data(focus="竞赛题型"),
    },
]


def _sync_existing_path_nodes(db) -> None:
    latest_by_key: dict[str, dict] = {}
    for template in DEFAULT_TEMPLATES:
        for phase in template["template_data"]["phases"]:
            for node in phase["nodes"]:
                latest_by_key[node["algorithm_key"]] = node

    for node in db.scalars(select(LearningPathNode)).all():
        source = latest_by_key.get(node.algorithm_key)
        if source is None:
            continue
        node.title = source["title"]
        node.summary = source["summary"]
        node.material_markdown = source["material_markdown"]
        node.resource_links = source["resource_links"]
        node.practice_items = source["practice_items"]


def seed_ladder_templates() -> None:
    with SessionLocal() as db:
        for item in DEFAULT_TEMPLATES:
            existing = db.scalar(
                select(LadderTemplate).where(
                    LadderTemplate.goal_track == item["goal_track"],
                    LadderTemplate.current_level == item["current_level"],
                    LadderTemplate.version == 1,
                )
            )
            if existing is None:
                existing = LadderTemplate(
                    goal_track=item["goal_track"],
                    current_level=item["current_level"],
                    version=1,
                )
                db.add(existing)
            existing.name = item["name"]
            existing.description = item["description"]
            existing.template_data = item["template_data"]
            existing.is_default = True
        _sync_existing_path_nodes(db)
        db.commit()


if __name__ == "__main__":
    seed_ladder_templates()
