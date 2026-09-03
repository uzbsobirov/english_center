import asyncio
from backend.database import async_session
from backend.models import User
from backend.services.user_service import is_admin_or_manager, is_teacher

async def check_user():
    user_id = 1435473812
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            print(f"User {user_id} not found in DB table 'users'.")
        else:
            print(f"ID: {user.id}")
            print(f"Full Name: {user.full_name}")
            print(f"Username: @{user.username}")
            print(f"Phone: {user.phone}")
            print(f"Role in DB: {user.role.value if hasattr(user.role, 'value') else user.role}")
            print(f"is_active: {user.is_active}")
            
    is_admin = await is_admin_or_manager(user_id)
    is_t = await is_teacher(user_id)
    print(f"is_admin_or_manager: {is_admin}")
    print(f"is_teacher: {is_t}")

if __name__ == "__main__":
    asyncio.run(check_user())
