from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app import models
from app.database import SessionLocal
from app.services.security import hash_password
from app.database import Base, SessionLocal, engine


def main() -> None:
    print("Create manager account")
    print("----------------------")

    Base.metadata.create_all(bind=engine)

    full_name = input("Manager full name: ").strip()
    email = input("Manager email: ").strip().lower()
    password = getpass("Manager password: ")
    confirm_password = getpass("Confirm password: ")

    if len(full_name) < 2:
        print("Full name must contain at least 2 characters.")
        return

    if "@" not in email:
        print("Enter a valid email address.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        statement = select(models.User).where(
            models.User.email == email
        )

        existing_user = db.scalar(statement)

        if existing_user is not None:
            print("A user with this email already exists.")
            return

        manager = models.User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=models.UserRole.MANAGER,
            is_active=True,
        )

        db.add(manager)
        db.commit()
        db.refresh(manager)

        print()
        print("Manager created successfully.")
        print(f"User ID: {manager.id}")
        print(f"Email: {manager.email}")
        print(f"Role: {manager.role.value}")

    except SQLAlchemyError as exc:
        db.rollback()
        print(f"Database error: {exc}")

    finally:
        db.close()


if __name__ == "__main__":
    main()