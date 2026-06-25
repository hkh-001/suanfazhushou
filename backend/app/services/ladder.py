from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ladder import LadderTemplate, LearningPath, LearningPathNode, NodeUserProgress
from app.models.user import User
from app.repositories.ladder import (
    create_path_with_nodes,
    get_active_path,
    get_default_template,
    get_path_node_for_user,
    get_progress_for_path,
    get_published_topic_by_slug,
    mark_material_completed,
    mark_practice_completed,
)
from app.schemas.ladder import (
    LadderChoicePracticeItem,
    LadderChoiceResult,
    LadderCodingPracticeItem,
    LadderNodeDetail,
    LadderNodeStatus,
    LadderNodeSummary,
    LadderPathSummary,
    LadderPhase,
    LadderPracticeItem,
    LadderPracticeSubmitRequest,
    LadderPracticeSubmitResult,
    LadderResourceLink,
    LadderSummary,
)


LADDER_TEMPLATE_NOT_FOUND = {
    "code": "LADDER_TEMPLATE_NOT_FOUND",
    "message": "Learning ladder template not found",
}
LADDER_NODE_NOT_FOUND = {"code": "LADDER_NODE_NOT_FOUND", "message": "Learning ladder node not found"}
LADDER_PATH_CREATE_FAILED = {
    "code": "LADDER_PATH_CREATE_FAILED",
    "message": "Learning ladder path could not be created",
}
NODE_LOCKED = {"code": "NODE_LOCKED", "message": "Learning ladder node is locked"}
NODE_MATERIAL_REQUIRED = {
    "code": "NODE_MATERIAL_REQUIRED",
    "message": "Learning ladder node material must be completed before practice",
}
LADDER_PRACTICE_NOT_FOUND = {
    "code": "LADDER_PRACTICE_NOT_FOUND",
    "message": "Learning ladder practice items not found",
}
LADDER_PRACTICE_VALIDATION_ERROR = {
    "code": "LADDER_PRACTICE_VALIDATION_ERROR",
    "message": "Learning ladder practice submission is invalid",
}
PRACTICE_PASS_SCORE = 80

LEVEL_FALLBACKS = {
    "improvement": ["improvement", "popularization", "elementary", "beginner"],
    "popularization": ["popularization", "elementary", "beginner"],
    "elementary": ["elementary", "beginner"],
    "beginner": ["beginner"],
}


@dataclass(frozen=True)
class PhaseMeta:
    title: str
    description: str | None = None


def _level_candidates(current_level: str) -> list[str]:
    return LEVEL_FALLBACKS.get(current_level, ["beginner"])


def _select_template(db: Session, *, goal_track: str, current_level: str) -> LadderTemplate:
    checked: set[tuple[str, str]] = set()
    for track, levels in (
        (goal_track, _level_candidates(current_level)),
        ("self_study", _level_candidates(current_level)),
        ("self_study", ["beginner"]),
    ):
        for level in levels:
            key = (track, level)
            if key in checked:
                continue
            checked.add(key)
            template = get_default_template(db, goal_track=track, current_level=level)
            if template is not None:
                return template
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_TEMPLATE_NOT_FOUND)


def _template_phases(template: LadderTemplate) -> list[dict]:
    phases = template.template_data.get("phases") if isinstance(template.template_data, dict) else None
    if not isinstance(phases, list) or not phases:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=LADDER_TEMPLATE_NOT_FOUND)
    return phases


def _phase_meta(path: LearningPath) -> dict[int, PhaseMeta]:
    if path.template is None:
        return {}
    result: dict[int, PhaseMeta] = {}
    try:
        phases = _template_phases(path.template)
    except HTTPException:
        return result
    for index, phase in enumerate(phases, start=1):
        if not isinstance(phase, dict):
            continue
        title = str(phase.get("title") or f"Phase {index}")
        description = phase.get("description")
        result[index] = PhaseMeta(title=title, description=str(description) if description else None)
    return result


def _resource_links(raw_links: object) -> list[dict]:
    if not isinstance(raw_links, list):
        return []
    links: list[dict] = []
    for item in raw_links:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        source = str(item.get("source") or "").strip() or None
        if title and url:
            links.append({"title": title[:120], "url": url[:500], "source": source[:80] if source else None})
    return links


def _practice_validation_error(status_code: int = 422) -> HTTPException:
    return HTTPException(status_code=status_code, detail=LADDER_PRACTICE_VALIDATION_ERROR)


def _public_practice_items(raw_items: object) -> list[LadderPracticeItem]:
    if not isinstance(raw_items, list):
        raise _practice_validation_error(status.HTTP_500_INTERNAL_SERVER_ERROR)

    seen_ids: set[str] = set()
    public_items: list[LadderPracticeItem] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise _practice_validation_error(status.HTTP_500_INTERNAL_SERVER_ERROR)
        item_id = str(raw_item.get("id") or "").strip()
        if not item_id or item_id in seen_ids:
            raise _practice_validation_error(status.HTTP_500_INTERNAL_SERVER_ERROR)
        seen_ids.add(item_id)

        item_type = raw_item.get("type")
        if item_type == "choice":
            options = raw_item.get("options")
            correct_option_id = str(raw_item.get("correct_option_id") or "").strip()
            if not isinstance(options, list) or not correct_option_id:
                raise _practice_validation_error(status.HTTP_500_INTERNAL_SERVER_ERROR)
            option_ids = [str(option.get("id") or "").strip() for option in options if isinstance(option, dict)]
            if len(option_ids) != len(set(option_ids)) or correct_option_id not in set(option_ids):
                raise _practice_validation_error(status.HTTP_500_INTERNAL_SERVER_ERROR)
            public_items.append(
                LadderChoicePracticeItem.model_validate(
                    {
                        "id": item_id,
                        "type": "choice",
                        "prompt": raw_item.get("prompt"),
                        "options": options,
                    }
                )
            )
        elif item_type == "coding":
            public_items.append(
                LadderCodingPracticeItem.model_validate(
                    {
                        "id": item_id,
                        "type": "coding",
                        "prompt": raw_item.get("prompt"),
                        "self_check": raw_item.get("self_check"),
                    }
                )
            )
        else:
            raise _practice_validation_error(status.HTTP_500_INTERNAL_SERVER_ERROR)
    return public_items


def _practice_items(raw_items: object) -> list[dict]:
    if raw_items is None:
        return []
    _public_practice_items(raw_items)
    assert isinstance(raw_items, list)
    return raw_items


def _choice_items(raw_items: list[dict]) -> list[dict]:
    return [item for item in raw_items if item.get("type") == "choice"]


def _coding_items(raw_items: list[dict]) -> list[dict]:
    return [item for item in raw_items if item.get("type") == "coding"]


def _nodes_from_template(db: Session, template: LadderTemplate) -> list[LearningPathNode]:
    nodes: list[LearningPathNode] = []
    node_index = 1
    for phase_index, phase in enumerate(_template_phases(template), start=1):
        if not isinstance(phase, dict):
            continue
        raw_nodes = phase.get("nodes")
        if not isinstance(raw_nodes, list):
            continue
        for raw_node in raw_nodes:
            if not isinstance(raw_node, dict):
                continue
            topic_id = None
            topic_slug = raw_node.get("topic_slug")
            if isinstance(topic_slug, str) and topic_slug.strip():
                topic = get_published_topic_by_slug(db, slug=topic_slug.strip())
                topic_id = topic.id if topic is not None else None
            nodes.append(
                LearningPathNode(
                    topic_id=topic_id,
                    phase_index=phase_index,
                    node_index=node_index,
                    algorithm_key=str(raw_node.get("algorithm_key") or f"node-{node_index}")[:120],
                    title=str(raw_node.get("title") or f"Node {node_index}")[:120],
                    summary=str(raw_node.get("summary") or "Read the material and complete this learning node."),
                    material_markdown=str(raw_node.get("material_markdown") or "No material is available yet."),
                    resource_links=_resource_links(raw_node.get("resource_links")),
                    practice_items=_practice_items(raw_node.get("practice_items")),
                    unlock_rule={},
                )
            )
            node_index += 1
    if not nodes:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=LADDER_TEMPLATE_NOT_FOUND)
    return nodes


def _progress_map(db: Session, path: LearningPath, *, user_id: UUID) -> dict[UUID, NodeUserProgress]:
    return get_progress_for_path(db, path=path, user_id=user_id)


def _is_unlocked(node: LearningPathNode, nodes: list[LearningPathNode], progress_by_node: dict[UUID, NodeUserProgress]) -> bool:
    if node.node_index == 1:
        return True
    previous = next((candidate for candidate in nodes if candidate.node_index == node.node_index - 1), None)
    if previous is None:
        return False
    previous_progress = progress_by_node.get(previous.id)
    return bool(previous_progress and previous_progress.material_completed)


def _node_status(
    node: LearningPathNode,
    nodes: list[LearningPathNode],
    progress_by_node: dict[UUID, NodeUserProgress],
) -> LadderNodeStatus:
    progress = progress_by_node.get(node.id)
    if progress is not None and progress.exam_passed:
        return "passed"
    if progress is not None and progress.practice_completed:
        return "practice_done"
    if progress is not None and progress.material_completed:
        return "material_done"
    return "unlocked" if _is_unlocked(node, nodes, progress_by_node) else "locked"


def _node_summary(
    node: LearningPathNode,
    nodes: list[LearningPathNode],
    progress_by_node: dict[UUID, NodeUserProgress],
) -> LadderNodeSummary:
    progress = progress_by_node.get(node.id)
    node_status = _node_status(node, nodes, progress_by_node)
    return LadderNodeSummary(
        id=node.id,
        topic_id=node.topic_id,
        phase_index=node.phase_index,
        node_index=node.node_index,
        algorithm_key=node.algorithm_key,
        title=node.title,
        summary=node.summary,
        status=node_status,
        locked=node_status == "locked",
        material_completed=bool(progress and progress.material_completed),
        practice_completed=bool(progress and progress.practice_completed),
        exam_passed=bool(progress and progress.exam_passed),
    )


def _to_summary(db: Session, path: LearningPath, *, user_id: UUID) -> LadderSummary:
    nodes = sorted(path.nodes, key=lambda node: node.node_index)
    progress_by_node = _progress_map(db, path, user_id=user_id)
    phase_meta = _phase_meta(path)
    summaries = [_node_summary(node, nodes, progress_by_node) for node in nodes]

    phases: list[LadderPhase] = []
    for phase_index in sorted({node.phase_index for node in nodes}):
        meta = phase_meta.get(phase_index, PhaseMeta(title=f"Phase {phase_index}"))
        phases.append(
            LadderPhase(
                phase_index=phase_index,
                title=meta.title,
                description=meta.description,
                nodes=[node for node in summaries if node.phase_index == phase_index],
            )
        )

    current = next((node for node in summaries if not node.locked and not node.material_completed), None)
    if current is None:
        current = next((node for node in summaries if not node.locked and not node.exam_passed), None)
    if current is None and summaries:
        current = summaries[0]

    return LadderSummary(
        path=LadderPathSummary(
            id=path.id,
            status=path.status,
            goal_track=path.goal_track,
            current_level=path.current_level,
            template_name=path.template.name if path.template is not None else "Learning Path",
            created_at=path.created_at,
        ),
        phases=phases,
        current_node_id=current.id if current is not None else None,
    )


def get_or_create_ladder(db: Session, *, user: User) -> LadderSummary:
    existing = get_active_path(db, user_id=user.id)
    if existing is not None:
        return _to_summary(db, existing, user_id=user.id)

    template = _select_template(
        db,
        goal_track=(user.goal_track or "self_study"),
        current_level=(user.current_level or "beginner"),
    )
    try:
        path = create_path_with_nodes(db, user_id=user.id, template=template, nodes=_nodes_from_template(db, template))
    except IntegrityError as exc:
        db.rollback()
        existing = get_active_path(db, user_id=user.id)
        if existing is not None:
            return _to_summary(db, existing, user_id=user.id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_PATH_CREATE_FAILED) from exc
    return _to_summary(db, path, user_id=user.id)


def get_ladder_node(db: Session, *, user: User, node_id: UUID) -> LadderNodeDetail:
    node = get_path_node_for_user(db, node_id=node_id, user_id=user.id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)
    nodes = sorted(node.path.nodes, key=lambda item: item.node_index)
    progress_by_node = _progress_map(db, node.path, user_id=user.id)
    summary = _node_summary(node, nodes, progress_by_node)
    progress = progress_by_node.get(node.id)
    return LadderNodeDetail(
        **summary.model_dump(),
        path_id=node.path_id,
        material_markdown=node.material_markdown,
        resource_links=[LadderResourceLink.model_validate(link) for link in node.resource_links],
        practice_items=_public_practice_items(node.practice_items),
        practice_completed_at=progress.practice_completed_at if progress is not None else None,
    )


def complete_ladder_node_material(db: Session, *, user: User, node_id: UUID) -> LadderSummary:
    node = get_path_node_for_user(db, node_id=node_id, user_id=user.id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)
    nodes = sorted(node.path.nodes, key=lambda item: item.node_index)
    progress_by_node = _progress_map(db, node.path, user_id=user.id)
    if _node_status(node, nodes, progress_by_node) == "locked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NODE_LOCKED)
    progress = progress_by_node.get(node.id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)
    mark_material_completed(db, progress)
    refreshed = get_active_path(db, user_id=user.id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_PATH_CREATE_FAILED)
    return _to_summary(db, refreshed, user_id=user.id)


def submit_ladder_node_practice(
    db: Session,
    *,
    user: User,
    node_id: UUID,
    payload: LadderPracticeSubmitRequest,
) -> LadderPracticeSubmitResult:
    node = get_path_node_for_user(db, node_id=node_id, user_id=user.id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)

    nodes = sorted(node.path.nodes, key=lambda item: item.node_index)
    progress_by_node = _progress_map(db, node.path, user_id=user.id)
    node_status = _node_status(node, nodes, progress_by_node)
    if node_status == "locked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NODE_LOCKED)

    progress = progress_by_node.get(node.id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)
    if not progress.material_completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NODE_MATERIAL_REQUIRED)

    raw_items = node.practice_items if isinstance(node.practice_items, list) else []
    if not raw_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_PRACTICE_NOT_FOUND)
    _public_practice_items(raw_items)

    choice_items = _choice_items(raw_items)
    coding_items = _coding_items(raw_items)
    choice_by_id = {item["id"]: item for item in choice_items}
    coding_ids = {item["id"] for item in coding_items}

    answer_map: dict[str, str] = {}
    for answer in payload.choice_answers:
        if answer.item_id in answer_map:
            raise _practice_validation_error()
        if answer.item_id not in choice_by_id:
            raise _practice_validation_error()
        option_ids = {
            str(option.get("id") or "").strip()
            for option in choice_by_id[answer.item_id].get("options", [])
            if isinstance(option, dict)
        }
        if answer.option_id not in option_ids:
            raise _practice_validation_error()
        answer_map[answer.item_id] = answer.option_id

    completed_coding_ids = set(payload.completed_coding_item_ids)
    if len(completed_coding_ids) != len(payload.completed_coding_item_ids):
        raise _practice_validation_error()
    if not completed_coding_ids.issubset(coding_ids):
        raise _practice_validation_error()

    correct_count = 0
    choice_results: list[LadderChoiceResult] = []
    for item in choice_items:
        item_id = str(item["id"])
        correct = answer_map.get(item_id) == str(item.get("correct_option_id") or "").strip()
        if correct:
            correct_count += 1
        explanation = str(item.get("explanation") or "").strip() or None
        choice_results.append(LadderChoiceResult(item_id=item_id, correct=correct, explanation=explanation))

    score = round(correct_count / len(choice_items) * 100) if choice_items else 100
    coding_complete = coding_ids.issubset(completed_coding_ids)
    passed = (score >= PRACTICE_PASS_SCORE and coding_complete) or progress.practice_completed

    if passed and not progress.practice_completed:
        mark_practice_completed(db, progress)

    refreshed = get_active_path(db, user_id=user.id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_PATH_CREATE_FAILED)
    refreshed_progress = _progress_map(db, refreshed, user_id=user.id).get(node_id)
    return LadderPracticeSubmitResult(
        score=score,
        passed=passed,
        practice_completed=bool(refreshed_progress and refreshed_progress.practice_completed),
        choice_results=choice_results,
        ladder=_to_summary(db, refreshed, user_id=user.id),
    )
