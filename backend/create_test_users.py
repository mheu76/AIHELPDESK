"""
Create test users for development.
Run this script to populate the database with test accounts.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.db.base import Base


async def create_test_users():
    """Create test users in the database"""

    # Create engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Test accounts
        test_accounts = [
            {
                "employee_id": "TEST001",
                "email": "test@company.com",
                "name": "Test User",
                "password": "Test123!@#",
                "role": UserRole.EMPLOYEE,
            },
            {
                "employee_id": "IT001",
                "email": "it@company.com",
                "name": "IT Staff",
                "password": "IT123!@#",
                "role": UserRole.IT_STAFF,
            },
            {
                "employee_id": "ADMIN001",
                "email": "admin@company.com",
                "name": "Admin User",
                "password": "Admin123!@#",
                "role": UserRole.ADMIN,
            },
        ]

        for account in test_accounts:
            # Check if user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.employee_id == account["employee_id"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"✓ User {account['employee_id']} already exists, skipping...")
                continue

            # Create user
            user = User(
                employee_id=account["employee_id"],
                email=account["email"],
                name=account["name"],
                hashed_password=get_password_hash(account["password"]),
                role=account["role"],
            )
            session.add(user)
            print(f"✓ Created user: {account['employee_id']} ({account['role'].value})")

        await session.commit()

    await engine.dispose()

    print("\n" + "="*60)
    print("Test users created successfully!")
    print("="*60)
    print("\nTest Accounts:")
    print("-" * 60)
    print(f"{'Role':<15} {'Employee ID':<15} {'Password':<20}")
    print("-" * 60)
    print(f"{'Employee':<15} {'TEST001':<15} {'Test123!@#':<20}")
    print(f"{'IT Staff':<15} {'IT001':<15} {'IT123!@#':<20}")
    print(f"{'Admin':<15} {'ADMIN001':<15} {'Admin123!@#':<20}")
    print("-" * 60)


if __name__ == "__main__":
    print("Creating test users...")
    asyncio.run(create_test_users())
