from datetime import datetime, timezone
from pathlib import Path
import sys

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


ADMIN_STUDENT_ID = "admin"
ADMIN_EMAIL = "admin@algomentor.local"
ADMIN_USERNAME = "admin"


def main() -> None:
    password = settings.dev_admin_password.strip()
    if not password or password == "change_me_for_local_admin":
        print("DEV_ADMIN_PASSWORD is required before seeding the development admin account.")
        raise SystemExit(1)

    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.student_id == ADMIN_STUDENT_ID))
        values = {
            "email": ADMIN_EMAIL,
            "username": ADMIN_USERNAME,
            "hashed_password": hash_password(password),
            "student_id": ADMIN_STUDENT_ID,
            "name": "Admin",
            "current_level": "improvement",
            "goal_track": "self_study",
            "goal_description": "Development administrator account.",
            "onboarding_completed_at": datetime.now(timezone.utc),
            "role": "admin",
            "learning_stage": "improvement",
            "target_track": "self_study",
        }
        if admin is None:
            db.add(User(**values))
        else:
            for key, value in values.items():
                setattr(admin, key, value)
        db.commit()
    print("Seeded development admin account: admin")


if __name__ == "__main__":
    main()
