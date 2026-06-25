from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.ladder import LadderTemplate


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
    }
    if topic_slug:
        node["topic_slug"] = topic_slug
    return node


def _template_data(*, focus: str) -> dict:
    return {
        "phases": [
            {
                "title": "Foundation",
                "description": "Build the vocabulary and habits needed for algorithm practice.",
                "nodes": [
                    _node(
                        "time-complexity",
                        "Time Complexity",
                        "Learn to estimate running time before writing code.",
                        (
                            "# Time Complexity\n\n"
                            "Complexity analysis asks how the number of operations grows with input size. "
                            "For beginner practice, first distinguish constant, linear, logarithmic, and quadratic "
                            "growth. When solving a problem, write down the expected maximum input size and choose "
                            "an approach whose growth can finish in time.\n\n"
                            "## Checklist\n\n"
                            "- Identify the main loop or recursion.\n"
                            "- Count how often each element is processed.\n"
                            "- Compare the result with the input limit.\n"
                        ),
                        topic_slug="time-complexity",
                    ),
                    _node(
                        "array-and-string-basics",
                        "Arrays And Strings",
                        "Practice indexing, boundaries, and simple scans.",
                        (
                            "# Arrays And Strings\n\n"
                            "Most entry-level algorithm tasks are built on arrays and strings. "
                            "Focus on index ranges, off-by-one errors, and whether a scan should keep a running "
                            "state such as a sum, maximum, or frequency table.\n\n"
                            "## Practice habit\n\n"
                            "Before coding, write one small example and mark each index that will be visited."
                        ),
                        topic_slug="array-basics",
                    ),
                ],
            },
            {
                "title": focus,
                "description": "Move from basic tools to common contest patterns.",
                "nodes": [
                    _node(
                        "sorting",
                        "Sorting",
                        "Use ordering to simplify selection and counting tasks.",
                        (
                            "# Sorting\n\n"
                            "Sorting turns an unordered collection into a structure that is easier to reason about. "
                            "After sorting, adjacent elements often reveal duplicates, gaps, or best pairings.\n\n"
                            "## Common questions\n\n"
                            "- Does ordering change the answer?\n"
                            "- Can the sorted order make a greedy choice obvious?\n"
                            "- Is `O(n log n)` acceptable for the input size?"
                        ),
                        topic_slug="sorting",
                    ),
                    _node(
                        "two-pointers",
                        "Two Pointers",
                        "Maintain two moving indexes instead of nested loops.",
                        (
                            "# Two Pointers\n\n"
                            "Two pointers reduce repeated work by moving indexes monotonically. "
                            "They are useful on sorted arrays, intervals, and window-like conditions.\n\n"
                            "## Key idea\n\n"
                            "Each pointer should move only forward when possible. If a pointer can move backward "
                            "many times, the algorithm may no longer be linear."
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
        "name": "Self-study Beginner Path",
        "description": "A compact path for independent algorithm foundations.",
        "template_data": _template_data(focus="Core Patterns"),
    },
    {
        "goal_track": "course",
        "current_level": "beginner",
        "name": "Course Support Beginner Path",
        "description": "A path for strengthening programming-course fundamentals.",
        "template_data": _template_data(focus="Course Practice"),
    },
    {
        "goal_track": "lanqiao",
        "current_level": "elementary",
        "name": "Lanqiao Elementary Path",
        "description": "A path for preparing common Lanqiao Cup algorithm patterns.",
        "template_data": _template_data(focus="Lanqiao Patterns"),
    },
    {
        "goal_track": "icpc",
        "current_level": "popularization",
        "name": "ICPC Popularization Path",
        "description": "A path for moving from basic contest patterns toward ICPC preparation.",
        "template_data": _template_data(focus="Contest Patterns"),
    },
]


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
        db.commit()


if __name__ == "__main__":
    seed_ladder_templates()
