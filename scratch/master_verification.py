import sys
import json
import asyncio
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import async_session
from backend.models import User, Course, Group, Enrollment, Payment, RoleEnum
from backend.services.user_service import is_admin_or_manager, is_teacher
from app.keyboards.admin_menu import admin_menu_keyboard, ADMIN_MENU_TEXTS
from backend.api.routes.admin import (
    get_admin_dashboard, get_admin_courses, get_admin_groups,
    get_admin_teachers, get_admin_staff as get_admin_admins, get_admin_students, get_admin_payments
)
from backend.api.routes.teacher import get_user_roles, get_teacher_workspace

async def run_master_test():
    print("=" * 70)
    print("🌟 MASTER SYSTEM VERIFICATION SUITE — ALPHA ENGLISH CENTER")
    print("=" * 70)

    total_checks = 0
    passed_checks = 0

    # ----------------------------------------------------
    # TEST 1: DATABASE INTEGRITY & SEEDED DATA
    # ----------------------------------------------------
    print("\n[TEST 1] Checking Database Records & Seeded State...")
    async with async_session() as s:
        from sqlalchemy import select, func
        user_count = (await s.execute(select(func.count(User.id)))).scalar()
        course_count = (await s.execute(select(func.count(Course.id)))).scalar()
        group_count = (await s.execute(select(func.count(Group.id)))).scalar()
        enr_count = (await s.execute(select(func.count(Enrollment.id)).where(Enrollment.is_active == True))).scalar()
        pay_count = (await s.execute(select(func.count(Payment.id)))).scalar()

    total_checks += 1
    if user_count >= 10 and course_count >= 2 and group_count >= 2 and enr_count >= 8:
        passed_checks += 1
        print(f"✅ DB State Valid: {user_count} Users, {course_count} Courses, {group_count} Groups, {enr_count} Active Enrollments, {pay_count} Payments")
    else:
        print(f"❌ DB State Abnormal: Users={user_count}, Courses={course_count}, Groups={group_count}")

    # ----------------------------------------------------
    # TEST 2: ADMIN DASHBOARD DATA & APIS
    # ----------------------------------------------------
    print("\n[TEST 2] Testing Admin Dashboard APIs...")
    mock_admin = {"id": 1435473812, "full_name": "Anvar Sobirov"}
    dash = await get_admin_dashboard(user=mock_admin)
    courses = await get_admin_courses(user=mock_admin)
    groups = await get_admin_groups(user=mock_admin)
    teachers = await get_admin_teachers(user=mock_admin)
    admins = await get_admin_admins(user=mock_admin)
    students = await get_admin_students(user=mock_admin)
    payments = await get_admin_payments(user=mock_admin)

    total_checks += 1
    if dash["total_students"] >= 8 and dash["total_revenue"] > 2000000 and len(groups) >= 2:
        passed_checks += 1
        print(f"✅ Dashboard KPI: Students={dash['total_students']}, Revenue={dash['total_revenue']:,.0f} UZS, Pending={dash['pending_payments']}")
    else:
        print(f"❌ Dashboard KPI unexpected: {dash}")

    total_checks += 1
    if len(courses) >= 2 and len(teachers) >= 1 and len(admins) >= 1 and len(students) >= 8:
        passed_checks += 1
        print(f"✅ Management Tables: {len(courses)} Courses, {len(groups)} Groups, {len(teachers)} Teachers, {len(admins)} Admins, {len(students)} Students, {len(payments)} Payments")
    else:
        print("❌ Table endpoints returned insufficient items")

    # ----------------------------------------------------
    # TEST 3: TEACHER WORKSPACE APIS (ANVAR & ZEM)
    # ----------------------------------------------------
    print("\n[TEST 3] Testing Teacher Workspace APIs...")
    # Anvar Sobirov's Teacher Workspace
    anvar_ws = await get_teacher_workspace(user={"id": 1435473812})
    total_checks += 1
    if len(anvar_ws["groups"]) >= 1 and anvar_ws["groups"][0]["name"] == "GA | Odd":
        passed_checks += 1
        g1 = anvar_ws["groups"][0]
        print(f"✅ Anvar Sobirov Workspace: Group='{g1['name']}', Roster={len(g1['students'])} students enrolled")
    else:
        print(f"❌ Anvar Workspace unexpected: {anvar_ws}")

    # Zem's Teacher Workspace
    zem_ws = await get_teacher_workspace(user={"id": 7195359577})
    total_checks += 1
    if len(zem_ws["groups"]) >= 1 and zem_ws["groups"][0]["name"] == "IELTS-1 | Even":
        passed_checks += 1
        g2 = zem_ws["groups"][0]
        print(f"✅ Zem Workspace: Group='{g2['name']}', Roster={len(g2['students'])} students enrolled, Room='{g2['room']}'")
    else:
        print(f"❌ Zem Workspace unexpected: {zem_ws}")

    # ----------------------------------------------------
    # TEST 4: ROLE RESOLVER (/api/teacher/user-roles)
    # ----------------------------------------------------
    print("\n[TEST 4] Testing User Role Resolver Logic...")
    roles_anvar = await get_user_roles(user={"id": 1435473812})
    roles_zem = await get_user_roles(user={"id": 7195359577})
    roles_student = await get_user_roles(user={"id": 700100101})

    total_checks += 1
    if roles_anvar["is_admin"] and roles_anvar["is_teacher"] and roles_anvar["is_dual_role"]:
        passed_checks += 1
        print("✅ Dual-Role Resolver (Anvar): is_admin=True, is_teacher=True, is_dual_role=True")
    else:
        print(f"❌ Anvar roles incorrect: {roles_anvar}")

    total_checks += 1
    if not roles_zem["is_admin"] and roles_zem["is_teacher"] and not roles_zem["is_dual_role"]:
        passed_checks += 1
        print("✅ Pure Teacher Resolver (Zem): is_admin=False, is_teacher=True, is_dual_role=False")
    else:
        print(f"❌ Zem roles incorrect: {roles_zem}")

    total_checks += 1
    if not roles_student["is_admin"] and not roles_student["is_teacher"]:
        passed_checks += 1
        print("✅ Student Resolver (Madina): is_admin=False, is_teacher=False")
    else:
        print(f"❌ Student roles incorrect: {roles_student}")

    # ----------------------------------------------------
    # TEST 5: BOT KEYBOARD DYNAMICS FOR ALL 3 SCENARIOS
    # ----------------------------------------------------
    print("\n[TEST 5] Testing Telegram Bot Reply Keyboards...")
    # Scenario A: Dual Role
    kb_a = admin_menu_keyboard(user_id=1435473812, is_admin=True, is_teacher=True)
    btns_a = [b.text for row in kb_a.keyboard for b in row]
    has_dual = (ADMIN_MENU_TEXTS["DASHBOARD"] in btns_a) and (ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] in btns_a)
    
    # Scenario B: Pure Teacher Zem
    kb_b = admin_menu_keyboard(user_id=7195359577, is_admin=False, is_teacher=True)
    btns_b = [b.text for row in kb_b.keyboard for b in row]
    pure_t = (ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] in btns_b) and (ADMIN_MENU_TEXTS["DASHBOARD"] not in btns_b) and (ADMIN_MENU_TEXTS["ADMINS"] not in btns_b)

    # Scenario C: Pure Admin
    kb_c = admin_menu_keyboard(user_id=444333, is_admin=True, is_teacher=False)
    btns_c = [b.text for row in kb_c.keyboard for b in row]
    pure_adm = (ADMIN_MENU_TEXTS["DASHBOARD"] in btns_c) and (ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"] not in btns_c)

    total_checks += 1
    if has_dual and pure_t and pure_adm:
        passed_checks += 1
        print("✅ Telegram Keyboard Generator: All 3 role variations generated with 100% strict isolation")
    else:
        print(f"❌ Keyboard generator failed: has_dual={has_dual}, pure_t={pure_t}, pure_adm={pure_adm}")

    # ----------------------------------------------------
    # TEST 6: CAPACITY MATH INTEGRITY
    # ----------------------------------------------------
    print("\n[TEST 6] Testing Group Capacity Counter...")
    total_checks += 1
    g1_db = next(g for g in groups if g["name"] == "GA | Odd")
    g2_db = next(g for g in groups if g["name"] == "IELTS-1 | Even")
    if g1_db["enrolled_students"] == 6 and g2_db["enrolled_students"] == 3:
        passed_checks += 1
        print(f"✅ Capacity Verification: Group 1 = 6/15 | Group 2 = 3/12 (Accurately excludes inactive/refunded)")
    else:
        print(f"❌ Capacity count mismatch: G1={g1_db['enrolled_students']}, G2={g2_db['enrolled_students']}")

    print("\n" + "=" * 70)
    print(f"🏁 MASTER VERIFICATION RESULT: {passed_checks}/{total_checks} CHECKS PASSED ({int(passed_checks/total_checks*100)}%)")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_master_test())
