import os

from app.core.bootstrap import create_admin
from app.core.database import SessionLocal


def main() -> None:
    email = os.environ["ADMIN_EMAIL"]
    password = os.environ["ADMIN_PASSWORD"]
    full_name = os.environ.get("ADMIN_NAME", "Administrator")
    db = SessionLocal()
    try:
        user = create_admin(db, email, full_name, password)
        print(f"Admin ready: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
