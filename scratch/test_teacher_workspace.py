import asyncio
from backend.api.routes.teacher import get_user_roles, get_teacher_workspace

async def test_teacher_api():
    mock_user = {"id": 1435473812, "full_name": "Anvar Sobirov"}
    
    roles = await get_user_roles(user=mock_user)
    print("User roles:", roles)
    assert roles["is_admin"] is True
    assert roles["is_teacher"] is True
    assert roles["is_dual_role"] is True
    
    workspace = await get_teacher_workspace(user=mock_user)
    print("Academic stats:", workspace["academic_stats"])
    print("Groups count:", len(workspace["groups"]))
    print("Teacher workspace verified successfully!")

if __name__ == "__main__":
    asyncio.run(test_teacher_api())
