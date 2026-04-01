"""
Update user role in database
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

from app.core.config import settings
from app.models.user import User, UserRole


async def update_role(employee_id: str, new_role: str):
    """Update user role"""

    # Validate role
    try:
        role_enum = UserRole(new_role)
    except ValueError:
        print(f"Invalid role: {new_role}")
        print(f"Valid roles: {[r.value for r in UserRole]}")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find user
        result = await session.execute(
            select(User).where(User.employee_id == employee_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ User {employee_id} not found")
            await engine.dispose()
            return

        # Update role
        user.role = role_enum
        await session.commit()

        print(f"✓ Updated {employee_id} role to {new_role}")

    await engine.dispose()


async def main():
    if len(sys.argv) < 3:
        print("Usage: python update_user_role.py <employee_id> <role>")
        print("\nExample:")
        print("  python update_user_role.py ADMIN001 admin")
        print("  python update_user_role.py IT001 it_staff")
        print("\nValid roles: employee, it_staff, admin")
        return

    employee_id = sys.argv[1]
    role = sys.argv[2]

    await update_role(employee_id, role)


if __name__ == "__main__":
    asyncio.run(main())
