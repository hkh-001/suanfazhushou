from __future__ import annotations

from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.ladder import LadderTemplate
from app.models.prompt_template import PromptTemplate
from app.models.topic import Topic
from app.models.user import User
from scripts import seed_admin, seed_ladder_templates, seed_prompt_templates, seed_topics


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_ADMIN_PASSWORD = "change_me_for_local_admin"


def run_migrations() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(config, "head")


def seed_base_data() -> None:
    seed_topics.main()
    seed_prompt_templates.main()
    seed_ladder_templates.seed_ladder_templates()


def should_seed_admin() -> bool:
    password = settings.dev_admin_password.strip()
    return bool(password) and password != PLACEHOLDER_ADMIN_PASSWORD


def seed_optional_admin() -> bool:
    if not should_seed_admin():
        print("Skipped admin seed: DEV_ADMIN_PASSWORD is not configured.")
        return False
    seed_admin.main()
    return True


def print_summary(*, admin_seeded: bool) -> None:
    with SessionLocal() as db:
        topic_count = db.scalar(select(func.count()).select_from(Topic)) or 0
        prompt_count = db.scalar(select(func.count()).select_from(PromptTemplate)) or 0
        ladder_template_count = db.scalar(select(func.count()).select_from(LadderTemplate)) or 0
        admin_exists = db.scalar(select(User).where(User.student_id == "admin", User.role == "admin")) is not None
    print("Development database initialization complete.")
    print(f"- topics: {topic_count}")
    print(f"- prompt templates: {prompt_count}")
    print(f"- ladder templates: {ladder_template_count}")
    print(f"- admin: {'seeded' if admin_seeded or admin_exists else 'skipped'}")


def main() -> None:
    print("Running Alembic migrations...")
    run_migrations()
    print("Seeding local development data...")
    seed_base_data()
    admin_seeded = seed_optional_admin()
    print_summary(admin_seeded=admin_seeded)


if __name__ == "__main__":
    main()
