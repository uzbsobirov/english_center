import sys
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from backend.database import async_session
from backend.models import User, RoleEnum, Group, Course, Enrollment, Payment
from backend.services.user_service import is_admin_or_manager, is_teacher
from app.keyboards.admin_menu import admin_menu_keyboard, ADMIN_MENU_TEXTS
from backend.api.routes.teacher import get_user_roles, get_teacher_workspace
from backend.api.routes.admin import get_admin_dashboard, get_admin_groups, get_admin_staff

async def run_comprehensive_check():
    print("=" * 60)
    print("🧪 COMPREHENSIVE END-TO-END ROLE & ACCOUNT VERIFICATION")
    print("=" * 60)

    # 1. TEST ACCOUNT: 1435473812 (Admin + Assigned Teacher)
    print("\n--- 1. TESTING DUAL-ROLE ACCOUNT: 1435473812 (Anvar Sobirov) ---")
    user_id = 1435473812
    is_adm = await is_admin_or_manager(user_id)
    is_t = await is_teacher(user_id)
    print(f"Role Check: is_admin={is_adm}, is_teacher={is_t}")
    assert is_adm is True, "1435473812 should be an Admin!"
    assert is_t is True, "1435473812 should be recognized as a Teacher (can teach)!"

    # Telegram Keyboard Check for Dual-Role
    kb = admin_menu_keyboard(user_id=user_id, user_name="Anvar Sobirov", is_admin=is_adm, is_teacher=is_t)
    buttons = [btn.text for row in kb.keyboard for btn in row]
    print(f"Telegram Menu Buttons ({len(buttons)}): {buttons}")
    assert ADMIN_MENU_TEXTS["DASHBOARD"] in buttons, "Dual-role user must have Admin Dashboard button!"
    assert ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] in buttons, "Dual-role user must have Teacher Dashboard button!"
    assert ADMIN_MENU_TEXTS["ADMINS"] in buttons, "Admin must have Admins management button!"
    print("✅ Telegram Keyboard for Dual-Role Account: PASSED")

    # API Workspace & Dashboard Check
    mock_dual = {"id": user_id, "full_name": "Anvar Sobirov"}
    admin_dash = await get_admin_dashboard(user=mock_dual)
    print(f"Admin Dashboard Stats: Total Students={admin_dash['total_students']}, Revenue={admin_dash['total_revenue']}")
    
    teacher_ws = await get_teacher_workspace(user=mock_dual)
    print(f"Teacher Workspace Stats: Groups={teacher_ws['academic_stats']['total_groups']}, Students={teacher_ws['academic_stats']['total_students']}")
    assert len(teacher_ws["groups"]) > 0, "Teacher should see their assigned group(s)!"
    print(f"Teacher's group name: {teacher_ws['groups'][0]['name']}")
    print("✅ WebApp API Data for Dual-Role Account: PASSED")


    # 2. TEST ACCOUNT: Pure Teacher (e.g. Test Teacher ID: 555444333)
    print("\n--- 2. TESTING PURE TEACHER ACCOUNT (e.g. ID: 555444333) ---")
    teacher_id = 555444333
    # Check keyboard generated for pure teacher:
    kb_teacher = admin_menu_keyboard(user_id=teacher_id, user_name="Pure Teacher", is_admin=False, is_teacher=True)
    t_buttons = [btn.text for row in kb_teacher.keyboard for btn in row]
    print(f"Pure Teacher Buttons ({len(t_buttons)}): {t_buttons}")
    assert ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] in t_buttons, "Teacher must have Teacher Dashboard button!"
    assert ADMIN_MENU_TEXTS["DASHBOARD"] not in t_buttons, "Teacher MUST NOT see Admin Dashboard!"
    assert ADMIN_MENU_TEXTS["ADMINS"] not in t_buttons, "Teacher MUST NOT see Admins button!"
    assert ADMIN_MENU_TEXTS["CASH_PAYMENT"] not in t_buttons, "Teacher MUST NOT see Cashier!"
    assert ADMIN_MENU_TEXTS["REFUND"] not in t_buttons, "Teacher MUST NOT see Refund!"
    print("✅ Pure Teacher Keyboard Security & Isolation: PASSED")


    # 3. TEST ACCOUNT: Pure Admin (e.g. Manager ID: 444333222 who does NOT teach)
    print("\n--- 3. TESTING PURE ADMIN ACCOUNT (Manager who doesn't teach) ---")
    admin_id = 444333222
    kb_admin = admin_menu_keyboard(user_id=admin_id, user_name="Pure Admin", is_admin=True, is_teacher=False)
    a_buttons = [btn.text for row in kb_admin.keyboard for btn in row]
    print(f"Pure Admin Buttons ({len(a_buttons)}): {a_buttons}")
    assert ADMIN_MENU_TEXTS["DASHBOARD"] in a_buttons, "Admin must have Admin Dashboard!"
    assert ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] not in a_buttons, "Pure Admin without classes should not have Teacher Cabinet clutter!"
    assert ADMIN_MENU_TEXTS["ADMINS"] in a_buttons, "Admin must have Admins button!"
    print("✅ Pure Admin Keyboard: PASSED")


    # 4. TEST ACCOUNT: 7195359577 (Zem - Active Teacher in DB)
    print("\n--- 4. TESTING ACTIVE TEACHER ACCOUNT: 7195359577 (Zem) ---")
    async with async_session() as session:
        zem = await session.get(User, 7195359577)
        assert zem is not None, "User Zem must exist in DB!"
        assert zem.role == RoleEnum.teacher, "Zem is the active teacher in DB!"
        print(f"Teacher Zem verified in DB: role={zem.role}, active={zem.is_active}")

    zem_is_adm = await is_admin_or_manager(7195359577)
    zem_is_t = await is_teacher(7195359577)
    print(f"Zem permissions: is_admin={zem_is_adm}, is_teacher={zem_is_t}")
    assert zem_is_adm is False, "Zem must NOT have admin authority!"
    assert zem_is_t is True, "Zem must have teacher authority!"

    zem_kb = admin_menu_keyboard(user_id=7195359577, user_name="Zem", is_admin=zem_is_adm, is_teacher=zem_is_t)
    zem_buttons = [btn.text for row in zem_kb.keyboard for btn in row]
    print(f"Zem's Telegram Buttons ({len(zem_buttons)}): {zem_buttons}")
    assert ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] in zem_buttons, "Zem must receive Teacher Dashboard button!"
    assert ADMIN_MENU_TEXTS["DASHBOARD"] not in zem_buttons, "Zem must NOT receive Admin Dashboard button!"
    assert ADMIN_MENU_TEXTS["ADMINS"] not in zem_buttons, "Zem must NOT receive Admins button!"
    assert ADMIN_MENU_TEXTS["CASH_PAYMENT"] not in zem_buttons, "Zem must NOT receive Cashier button!"
    assert ADMIN_MENU_TEXTS["REFUND"] not in zem_buttons, "Zem must NOT receive Refund button!"
    print("✅ Active Teacher Zem Keyboard & Permissions: 100% SECURE & ISOLATED")

    print("\n" + "=" * 60)
    print("🎉 ALL ACCOUNT & ROLE SCENARIOS VERIFIED 100% SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_check())
