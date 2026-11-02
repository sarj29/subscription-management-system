
import os
from pathlib import Path

from dotenv import load_dotenv

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus

# Load the root .env file
ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


def seed_admin():
    email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@brightloop.com")
    password = os.getenv("INITIAL_ADMIN_PASSWORD")

    if not password:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD is missing from .env")

    db_generator = get_db()
    db = next(db_generator)

    try:
        admin = db.query(User).filter(User.email == email).first()

        if admin:
            if admin.role != UserRole.ADMIN:
                raise RuntimeError(
                    f"{email} already exists but is not an admin. "
                    "Resolve this account manually."
                )

            print(f"Admin already exists: {email}")
            return

        admin = User(
            email=email,
            full_name="Brightloop Admin",
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )

        db.add(admin)
        db.commit()

        print(f"Admin created successfully: {email}")

    except Exception:
        db.rollback()
        raise

    finally:
        db_generator.close()


if __name__ == "__main__":
    seed_admin()
