from pathlib import Path
import sys

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.prompt_template import PromptTemplate


TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "app" / "prompts" / "templates"

TEMPLATES = [
    {
        "name": "Concept Explanation",
        "type": "concept_explanation",
        "version": 1,
        "template_key": "concept_explanation",
        "file_path": "concept_explanation.md",
        "input_schema_json": {"topic_context": "string", "mode": "string", "question": "string"},
        "output_schema_json": None,
    },
    {
        "name": "Code Review",
        "type": "code_review",
        "version": 1,
        "template_key": "code_review",
        "file_path": "code_review.md",
        "input_schema_json": {
            "topic_context": "string",
            "language": "string",
            "code": "string",
            "question": "string",
        },
        "output_schema_json": None,
    },
    {
        "name": "Problem Generation",
        "type": "problem_generation",
        "version": 1,
        "template_key": "problem_generation",
        "file_path": "problem_generation.md",
        "input_schema_json": {
            "topic_context": "string",
            "difficulty": "string",
            "requirements": "string",
        },
        "output_schema_json": {
            "title": "string",
            "statement": "string",
            "input_format": "string",
            "output_format": "string",
            "constraints": "string",
            "sample_input": "string",
            "sample_output": "string",
            "test_cases": [
                {
                    "name": "string",
                    "input": "string",
                    "expected_output": "string",
                    "is_sample": True,
                }
            ],
            "hints": ["string"],
            "solution_idea": "string",
            "solution_code_cpp": "string",
            "solution_code_python": "string",
            "is_ai_generated": True,
        },
    },
    {
        "name": "Submission Diagnosis",
        "type": "submission_diagnosis",
        "version": 1,
        "template_key": "submission_diagnosis",
        "file_path": "submission_diagnosis.md",
        "input_schema_json": {
            "verdict": "string",
            "language": "string",
            "problem_context": "string",
            "source_code": "string",
            "compile_output": "string",
            "error_message": "string",
            "case_context": "string",
        },
        "output_schema_json": None,
    },
    {
        "name": "Ladder Exam Generation",
        "type": "ladder_exam_generation",
        "version": 1,
        "template_key": "ladder_exam_generation",
        "file_path": "ladder_exam_generation.md",
        "input_schema_json": {
            "user_profile": "string",
            "node_title": "string",
            "node_summary": "string",
            "material_excerpt": "string",
            "practice_summary": "string",
            "difficulty_level": "string",
        },
        "output_schema_json": {
            "questions": [
                {
                    "id": "string",
                    "type": "single_choice | code_reading",
                    "prompt": "string",
                    "options": [{"id": "string", "text": "string"}],
                    "correct_option_id": "string",
                    "explanation": "string",
                }
            ]
        },
    },
]


def seed_prompt_templates() -> None:
    with SessionLocal() as db:
        for item in TEMPLATES:
            content = (TEMPLATE_ROOT / Path(item["file_path"]).name).read_text(encoding="utf-8")
            template = db.scalar(
                select(PromptTemplate).where(
                    PromptTemplate.template_key == item["template_key"],
                    PromptTemplate.version == item["version"],
                )
            )
            values = {**item, "content": content, "enabled": True}
            if template is None:
                db.add(PromptTemplate(**values))
            else:
                for key, value in values.items():
                    setattr(template, key, value)
        db.commit()


def main() -> None:
    seed_prompt_templates()
    print(f"Seeded {len(TEMPLATES)} prompt templates.")


if __name__ == "__main__":
    main()
