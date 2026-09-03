import asyncio
from backend.database import async_session
from backend.models import User, RoleEnum
from backend.api.routes.admin import get_admin_staff, StaffPayload, create_or_update_admin, delete_admin_staff

async def test_admin_api():
    mock_admin_user = {"id": 1435473812}
    
    # 1. Test get_admin_staff
    admins = await get_admin_staff(user=mock_admin_user)
    print("Fetched Admins:", len(admins))
    admin_ids = [a["id"] for a in admins]
    assert 1435473812 in admin_ids, "1435473812 should be in admins list!"
    print("Admin 1435473812 found in API list successfully!")
    
    # 2. Test create_or_update_admin
    payload = StaffPayload(
        telegram_id=999888777,
        full_name="Test Sub Admin",
        phone="+998901112233",
        username="subadmin_test"
    )
    res = await create_or_update_admin(payload, user=mock_admin_user)
    print("Create Admin result:", res)
    
    # Verify in list
    admins2 = await get_admin_staff(user=mock_admin_user)
    assert 999888777 in [a["id"] for a in admins2], "New admin should be in list!"
    print("New Admin 999888777 verified!")
    
    # 3. Test delete_admin_staff
    del_res = await delete_admin_staff(999888777, user=mock_admin_user)
    print("Delete Admin result:", del_res)
    
    # Verify demoted
    admins3 = await get_admin_staff(user=mock_admin_user)
    assert 999888777 not in [a["id"] for a in admins3], "Admin 999888777 should be removed!"
    print("All Admin API tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_admin_api())
