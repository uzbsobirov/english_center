import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { getTelegramLanguage, syncUserLanguage } from "../lib/telegram";
import { getTranslation } from "../lib/translations";
import LanguageSwitcher from "../components/LanguageSwitcher";
import TeacherDashboard from "./TeacherDashboard";

export default function AdminDashboard({ onSwitchMode }) {
  const [lang, setLang] = useState(getTelegramLanguage);
  const t = getTranslation(lang).admin || {};
  const [activeTab, setActiveTab] = useState("dashboard"); // dashboard, courses, groups, students, payments, broadcast
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Data states
  const [stats, setStats] = useState(null);
  const [courses, setCourses] = useState([]);
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [students, setStudents] = useState([]);
  const [payments, setPayments] = useState([]);
  const [paymentFilter, setPaymentFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Modals state
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [courseForm, setCourseForm] = useState({
    title_uz: "",
    title_ru: "",
    title_en: "",
    type: "General",
    level: "A1",
    price: "",
    price_per_lesson: "",
    duration_months: 1,
    lessons_per_week: 3,
    description_uz: "",
  });

  const [showGroupModal, setShowGroupModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [groupForm, setGroupForm] = useState({
    course_id: "",
    name: "",
    teacher_id: "",
    schedule_days: ["Monday", "Wednesday", "Friday"],
    schedule_time: "18:00",
    room: "1-xona",
    max_students: 12,
    group_chat_link: "",
    zoom_link: "",
  });

  const [showTeacherModal, setShowTeacherModal] = useState(false);
  const [teacherForm, setTeacherForm] = useState({
    telegram_id: "",
    full_name: "",
    phone: "",
    username: "",
  });

  const [showAdminModal, setShowAdminModal] = useState(false);
  const [adminForm, setAdminForm] = useState({
    telegram_id: "",
    full_name: "",
    phone: "",
    username: "",
  });

  // Broadcast state
  const [broadcastText, setBroadcastText] = useState("");
  const [broadcastRole, setBroadcastRole] = useState("all");
  const [broadcastLevel, setBroadcastLevel] = useState("");
  const [hasBroadcastBtn, setHasBroadcastBtn] = useState(false);
  const [broadcastBtnText, setBroadcastBtnText] = useState("");
  const [broadcastBtnUrl, setBroadcastBtnUrl] = useState("");
  const [broadcasting, setBroadcasting] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState(null);

  // Center Settings State
  const [centerSettings, setCenterSettings] = useState({
    contact_phone: "+998901234567",
    contact_username: "english_center_admin",
    address_uz: "Toshkent sh., Amir Temur ko'chasi, 12-uy",
    address_ru: "г. Ташкент, ул. Амира Темура, д. 12",
    address_en: "12 Amir Temur street, Tashkent",
    welcome_message_uz: "",
    welcome_message_ru: "",
    welcome_message_en: "",
  });
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsSuccess, setSettingsSuccess] = useState(false);
  const [userRoles, setUserRoles] = useState({ is_admin: true, is_teacher: false, is_dual_role: false });

  const handleLanguageChange = (newLang) => {
    setLang(newLang);
    syncUserLanguage(newLang);
  };

  const fetchDashboardData = () => {
    setLoading(true);
    setError(null);

    Promise.all([
      apiClient.get("/api/admin/dashboard").then((r) => setStats(r.data)),
      apiClient.get("/api/admin/courses").then((r) => setCourses(r.data)),
      apiClient.get("/api/admin/groups").then((r) => setGroups(r.data)),
      apiClient.get("/api/admin/teachers").then((r) => setTeachers(r.data)),
      apiClient.get("/api/admin/admins").then((r) => setAdmins(r.data)),
      apiClient.get("/api/admin/students").then((r) => setStudents(r.data)),
      apiClient.get("/api/admin/payments").then((r) => setPayments(r.data)),
      apiClient.get("/api/admin/settings").then((r) => setCenterSettings(r.data)).catch(() => {}),
      apiClient.get("/api/teacher/user-roles").then((r) => setUserRoles(r.data)).catch(() => {}),
    ])
      .catch((err) => {
        setError(err.response?.data?.detail || err.message);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Course Handlers
  const handleOpenCreateCourse = () => {
    setEditingCourse(null);
    setCourseForm({
      title_uz: "",
      title_ru: "",
      title_en: "",
      type: "General",
      level: "A1",
      price: "",
      price_per_lesson: "",
      duration_months: 1,
      lessons_per_week: 3,
      description_uz: "",
    });
    setShowCourseModal(true);
  };

  const handleOpenEditCourse = (c) => {
    setEditingCourse(c);
    setCourseForm({
      title_uz: c.title_uz || "",
      title_ru: c.title_ru || "",
      title_en: c.title_en || "",
      type: c.type || "General",
      level: c.level || "A1",
      price: c.price || "",
      price_per_lesson: c.price_per_lesson || "",
      duration_months: c.duration_months || 1,
      lessons_per_week: c.lessons_per_week || 3,
      description_uz: c.description_uz || "",
    });
    setShowCourseModal(true);
  };

  const handleSaveCourse = async (e) => {
    e.preventDefault();
    if (!courseForm.title_uz || !courseForm.price) {
      alert("Iltimos, kurs nomi va narxini kiriting!");
      return;
    }

    const payload = {
      ...courseForm,
      price: parseFloat(courseForm.price),
      price_per_lesson: courseForm.price_per_lesson ? parseFloat(courseForm.price_per_lesson) : null,
      duration_months: parseInt(courseForm.duration_months, 10),
      lessons_per_week: parseInt(courseForm.lessons_per_week, 10),
    };

    try {
      if (editingCourse) {
        await apiClient.put(`/api/admin/courses/${editingCourse.id}`, payload);
      } else {
        await apiClient.post("/api/admin/courses", payload);
      }
      setShowCourseModal(false);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Kursni saqlashda xatolik yuz berdi");
    }
  };

  const handleToggleCourse = async (courseId) => {
    try {
      await apiClient.delete(`/api/admin/courses/${courseId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    }
  };

  const WEEK_DAYS = [
    { id: "Monday", label: "Dush", full: "Dushanba" },
    { id: "Tuesday", label: "Sesh", full: "Seshanba" },
    { id: "Wednesday", label: "Chor", full: "Chorshanba" },
    { id: "Thursday", label: "Pay", full: "Payshanba" },
    { id: "Friday", label: "Jum", full: "Juma" },
    { id: "Saturday", label: "Shan", full: "Shanba" },
    { id: "Sunday", label: "Yak", full: "Yakshanba" },
  ];

  const handleToggleDay = (dayId) => {
    const currentDays = groupForm.schedule_days || [];
    if (currentDays.includes(dayId)) {
      if (currentDays.length > 1) {
        setGroupForm({
          ...groupForm,
          schedule_days: currentDays.filter((d) => d !== dayId),
        });
      }
    } else {
      setGroupForm({
        ...groupForm,
        schedule_days: [...currentDays, dayId],
      });
    }
  };

  const handleSetPresetDays = (presetDays) => {
    setGroupForm({
      ...groupForm,
      schedule_days: presetDays,
    });
  };

  // Group Handlers
  const handleOpenCreateGroup = () => {
    setEditingGroup(null);
    setGroupForm({
      course_id: courses[0]?.id || "",
      name: "",
      teacher_id: teachers[0]?.id || "",
      schedule_days: ["Monday", "Wednesday", "Friday"],
      schedule_time: "18:00",
      room: "1-xona",
      max_students: 12,
      group_chat_link: "",
      zoom_link: "",
    });
    setShowGroupModal(true);
  };

  const handleOpenEditGroup = (g) => {
    setEditingGroup(g);
    let parsedDays = ["Monday", "Wednesday", "Friday"];
    let parsedTime = "18:00";

    if (Array.isArray(g.schedule)) {
      parsedDays = g.schedule
        .map((item) => (typeof item === "object" ? item.day : item))
        .filter(Boolean);
      if (g.schedule.length > 0 && typeof g.schedule[0] === "object" && g.schedule[0].time) {
        parsedTime = g.schedule[0].time;
      }
    } else if (typeof g.schedule === "object" && g.schedule !== null) {
      if (g.schedule.days) {
        parsedDays = Array.isArray(g.schedule.days) ? g.schedule.days : [g.schedule.days];
      }
      if (g.schedule.time) {
        parsedTime = g.schedule.time;
      }
    }

    setGroupForm({
      course_id: g.course_id,
      name: g.name,
      teacher_id: g.teacher_id || "",
      schedule_days: parsedDays.length > 0 ? parsedDays : ["Monday", "Wednesday", "Friday"],
      schedule_time: parsedTime || "18:00",
      room: g.room || "1-xona",
      max_students: g.max_students || 12,
      group_chat_link: g.group_chat_link || "",
      zoom_link: g.zoom_link || "",
    });
    setShowGroupModal(true);
  };

  const handleSaveGroup = async (e) => {
    e.preventDefault();
    if (!groupForm.name || !groupForm.course_id) {
      alert("Iltimos, guruh nomi va kursni tanlang!");
      return;
    }

    const payload = {
      course_id: parseInt(groupForm.course_id, 10),
      name: groupForm.name,
      teacher_id: groupForm.teacher_id ? parseInt(groupForm.teacher_id, 10) : null,
      schedule_days: groupForm.schedule_days,
      schedule_time: groupForm.schedule_time,
      room: groupForm.room,
      max_students: parseInt(groupForm.max_students, 10),
      group_chat_link: groupForm.group_chat_link ? groupForm.group_chat_link.trim() : null,
      zoom_link: groupForm.zoom_link ? groupForm.zoom_link.trim() : null,
    };

    try {
      if (editingGroup) {
        await apiClient.put(`/api/admin/groups/${editingGroup.id}`, payload);
      } else {
        await apiClient.post("/api/admin/groups", payload);
      }
      setShowGroupModal(false);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Guruhni saqlashda xatolik yuz berdi");
    }
  };

  // Payment Actions
  const handleApprovePayment = async (paymentId) => {
    if (!confirm("Haqiqatan ham ushbu naqd to'lovni tasdiqlaysizmi?")) return;
    try {
      await apiClient.post(`/api/admin/payments/${paymentId}/approve`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    }
  };

  const handleRejectPayment = async (paymentId) => {
    if (!confirm("Ushbu to'lovni rad etmoqchimisiz?")) return;
    try {
      await apiClient.post(`/api/admin/payments/${paymentId}/reject`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    }
  };

  const handleSendBroadcast = async (e) => {
    e.preventDefault();
    if (!broadcastText.trim()) return;

    setBroadcasting(true);
    setBroadcastResult(null);

    try {
      const res = await apiClient.post("/api/admin/broadcast", {
        text: broadcastText,
        target_role: broadcastRole,
        level: broadcastLevel || null,
        button_text: hasBroadcastBtn && broadcastBtnText.trim() ? broadcastBtnText.trim() : null,
        button_url: hasBroadcastBtn && broadcastBtnUrl.trim() ? broadcastBtnUrl.trim() : null,
      });
      setBroadcastResult(res.data);
      setBroadcastText("");
      setBroadcastBtnText("");
      setBroadcastBtnUrl("");
      setHasBroadcastBtn(false);
    } catch (err) {
      alert(err.response?.data?.detail || "Xabar yuborishda xatolik");
    } finally {
      setBroadcasting(false);
    }
  };

  // Teacher Handlers
  const handleOpenCreateTeacher = () => {
    setTeacherForm({
      telegram_id: "",
      full_name: "",
      phone: "",
      username: "",
    });
    setShowTeacherModal(true);
  };

  const handleSaveTeacher = async (e) => {
    e.preventDefault();
    if (!teacherForm.telegram_id || !teacherForm.full_name) {
      alert("Iltimos, Telegram ID va Ism-familiyani kiriting!");
      return;
    }
    setLoading(true);
    try {
      await apiClient.post("/api/admin/teachers", {
        telegram_id: Number(teacherForm.telegram_id),
        full_name: teacherForm.full_name,
        phone: teacherForm.phone || null,
        username: teacherForm.username ? teacherForm.username.replace("@", "") : null,
      });
      setShowTeacherModal(false);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "O'qituvchini saqlashda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTeacher = async (tId, tName) => {
    if (!confirm(`${tName} o'qituvchilik vazifasidan ozod qilinsinmi?`)) return;
    setLoading(true);
    try {
      await apiClient.delete(`/api/admin/teachers/${tId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  // Admin Handlers
  const handleOpenCreateAdmin = () => {
    setAdminForm({
      telegram_id: "",
      full_name: "",
      phone: "",
      username: "",
    });
    setShowAdminModal(true);
  };

  const handleSaveAdmin = async (e) => {
    e.preventDefault();
    if (!adminForm.telegram_id || !adminForm.full_name) {
      alert("Iltimos, Telegram ID va Ism-familiyani kiriting!");
      return;
    }
    setLoading(true);
    try {
      await apiClient.post("/api/admin/admins", {
        telegram_id: Number(adminForm.telegram_id),
        full_name: adminForm.full_name,
        phone: adminForm.phone || null,
        username: adminForm.username ? adminForm.username.replace("@", "") : null,
      });
      setShowAdminModal(false);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Adminni saqlashda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAdmin = async (aId, aName) => {
    if (!confirm(`${aName} dan admin huquqlari olib tashlansinmi?`)) return;
    setLoading(true);
    try {
      await apiClient.delete(`/api/admin/admins/${aId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  const handleRefundPayment = async (paymentId) => {
    if (!confirm("Haqiqatan ham bu to'lovni qaytarmoqchimisiz (Refund)? O'quvchi rasman guruhdan chiqariladi.")) return;
    try {
      await apiClient.post(`/api/admin/payments/${paymentId}/refund`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Refund qilishda xatolik");
    }
  };

  // Filtered lists
  const filteredPayments = payments.filter((p) => {
    if (paymentFilter !== "all" && p.status !== paymentFilter) return false;
    if (searchTerm) {
      const sName = (p.student?.full_name || "").toLowerCase();
      const gName = (p.group?.name || "").toLowerCase();
      const term = searchTerm.toLowerCase();
      return sName.includes(term) || gName.includes(term);
    }
    return true;
  });

  const filteredStudents = students.filter((s) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (s.full_name || "").toLowerCase().includes(term) ||
      (s.phone || "").toLowerCase().includes(term) ||
      (s.username || "").toLowerCase().includes(term)
    );
  });

  const handleSaveCenterSettings = async (e) => {
    e.preventDefault();
    setSettingsSaving(true);
    setSettingsSuccess(false);
    try {
      await apiClient.put("/api/admin/settings", centerSettings);
      setSettingsSuccess(true);
      setTimeout(() => setSettingsSuccess(false), 3500);
    } catch (err) {
      alert(err.response?.data?.detail || "Sozlamalarni saqlashda xatolik");
    } finally {
      setSettingsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 pb-20 relative overflow-hidden font-sans">
      {/* Ambient glowing orbs */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/3 left-10 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header */}
      <header className="bg-[#0a0f1d]/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30 shadow-xl">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 to-indigo-600 flex items-center justify-center text-xl shadow-lg shadow-indigo-500/20">
              👑
            </div>
            <div>
              <h1 className="font-black text-white text-base leading-tight">
                {t.brandTitle || "Alpha Admin Dashboard"}
              </h1>
              <p className="text-[10px] text-slate-400 font-semibold">
                {t.brandSubtitle || "Markaz Boshqaruv Markazi"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <LanguageSwitcher currentLang={lang} onChangeLang={handleLanguageChange} />

            {onSwitchMode && userRoles.is_teacher && (
              <button
                onClick={() => onSwitchMode("teacher")}
                className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1.5"
                title={t.teacherCabinet || "Ustoz Kabineti"}
              >
                <span>👨‍🏫</span>
                <span className="hidden sm:inline">{t.teacherCabinet || "Ustoz Kabineti"}</span>
              </button>
            )}
            <button
              onClick={fetchDashboardData}
              className="p-2 text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 rounded-xl transition border border-slate-700/60"
              title={t.refresh || "Yangilash"}
            >
              🔄
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-6xl mx-auto px-4 flex gap-1.5 overflow-x-auto no-scrollbar border-t border-slate-800/80 pt-1 pb-1 text-xs font-bold">
          {[
            { id: "dashboard", label: t.tabs?.dashboard || "📊 Asosiy", badge: null },
            { id: "courses", label: t.tabs?.courses || "📚 Kurslar", badge: courses.length },
            { id: "groups", label: t.tabs?.groups || "👥 Guruhlar", badge: groups.length },
            ...(userRoles.is_teacher
              ? [{ id: "my_classes", label: t.tabs?.my_classes || "👨‍🏫 Mening Darslarim", badge: null }]
              : []),
            { id: "teachers", label: t.tabs?.teachers || "👨‍🏫 O'qituvchilar", badge: teachers.length },
            { id: "admins", label: t.tabs?.admins || "👑 Adminlar", badge: admins.length },
            { id: "students", label: t.tabs?.students || "🎓 O'quvchilar", badge: students.length },
            {
              id: "payments",
              label: t.tabs?.payments || "💳 To'lovlar",
              badge: stats?.pending_payments ? `${stats.pending_payments}` : null,
              badgeColor: "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse",
            },
            { id: "broadcast", label: t.tabs?.broadcast || "📢 Broadcast", badge: null },
            { id: "settings", label: t.tabs?.settings || "⚙️ Sozlamalar", badge: null },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2.5 px-3.5 whitespace-nowrap rounded-xl flex items-center gap-2 transition-all ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 font-black"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <span>{tab.label}</span>
                {tab.badge && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      tab.badgeColor || "bg-slate-800 text-slate-300 border border-slate-700"
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-4 space-y-5 relative z-10">
        {error && (
          <div className="glass-panel border border-red-500/30 text-red-300 p-4 rounded-2xl text-xs flex items-center justify-between shadow-xl">
            <span>⚠️ {error}</span>
            <button onClick={fetchDashboardData} className="underline font-black">
              Qayta urinish
            </button>
          </div>
        )}

        {/* 1. ASOSIY DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="space-y-5">
            {/* KPI Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
                <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">👥</span>
                <div className="text-2xl font-black text-white">
                  {stats?.total_students ?? 0}
                </div>
                <div className="text-[11px] text-slate-400 font-bold">O'quvchilar</div>
              </div>

              <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
                <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">📚</span>
                <div className="text-2xl font-black text-white">
                  {courses.length}
                </div>
                <div className="text-[11px] text-slate-400 font-bold">Kurslar</div>
              </div>

              <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
                <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">🏢</span>
                <div className="text-2xl font-black text-white">
                  {stats?.active_groups ?? 0}
                </div>
                <div className="text-[11px] text-slate-400 font-bold">Guruhlar</div>
              </div>

              <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
                <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">👨‍🏫</span>
                <div className="text-2xl font-black text-white">
                  {stats?.total_teachers ?? 0}
                </div>
                <div className="text-[11px] text-slate-400 font-bold">O'qituvchilar</div>
              </div>

              <div className="glass-card rounded-2xl p-4 border border-amber-500/30 shadow-xl relative overflow-hidden group">
                <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">⏳</span>
                <div className="text-2xl font-black text-amber-400">
                  {stats?.pending_payments ?? 0}
                </div>
                <div className="text-[11px] text-slate-400 font-bold">Kutilayotgan To'lov</div>
              </div>

              <div className="glass-card rounded-2xl p-4 border border-emerald-500/30 shadow-xl col-span-2 sm:col-span-1 relative overflow-hidden group">
                <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">💰</span>
                <div className="text-lg font-black text-emerald-400 truncate">
                  {(stats?.total_revenue ?? 0).toLocaleString()} <span className="text-xs font-bold">so'm</span>
                </div>
                <div className="text-[11px] text-slate-400 font-bold">Jami Tushum</div>
              </div>
            </div>

            {/* Banner Quick Actions */}
            <div className="relative rounded-3xl p-6 bg-gradient-to-r from-indigo-900/90 via-slate-900 to-purple-950/90 border border-indigo-500/30 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4 overflow-hidden">
              <div className="absolute right-0 top-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none"></div>

              <div>
                <h3 className="text-base font-black text-white mb-1">
                  {t.bannerTitle || "🚀 Alpha English Center — Boshqaruv Markazi"}
                </h3>
                <p className="text-xs text-slate-300 max-w-md leading-relaxed">
                  {t.bannerDesc || "Kurslar, guruhlar, to'lovlar, xodimlar hamda sun'iy intellekt (Gemini AI) testlarini markazlashtirilgan holda boshqaring."}
                </p>
              </div>
              <div className="flex flex-wrap gap-2 w-full sm:w-auto shrink-0">
                <button
                  onClick={handleOpenCreateCourse}
                  className="flex-1 sm:flex-none px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>➕</span>
                  <span>{t.newCourse || "Yangi Kurs"}</span>
                </button>
                <button
                  onClick={handleOpenCreateGroup}
                  className="flex-1 sm:flex-none px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-black text-xs rounded-xl transition active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>👥</span>
                  <span>{t.newGroup || "Yangi Guruh"}</span>
                </button>
                <button
                  onClick={handleOpenCreateAdmin}
                  className="flex-1 sm:flex-none px-4 py-2.5 bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition active:scale-95 flex items-center justify-center gap-1.5"
                >
                  <span>👑</span>
                  <span>{t.newAdmin || "Yangi Admin"}</span>
                </button>
              </div>
            </div>

            {/* Active Groups Overview */}
            <div className="glass-panel rounded-3xl p-5 border border-slate-800 shadow-2xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-black text-sm text-white flex items-center gap-2">
                  <span>🏢</span> Faol Guruhlar ({groups.length})
                </h3>
                <button
                  onClick={() => setActiveTab("groups")}
                  className="text-xs font-bold text-indigo-400 hover:underline"
                >
                  Barchasini ko'rish →
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {groups.slice(0, 6).map((g) => (
                  <div
                    key={g.id}
                    className="glass-card rounded-2xl p-4 border border-slate-800 hover:border-indigo-500/40 transition space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="font-black text-xs text-white">{g.name}</h4>
                      <span className="text-[10px] font-black px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {g.course?.type || "Course"}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 space-y-1">
                      <div>👨‍🏫 Ustoz: <b className="text-slate-200">{g.teacher?.full_name || "Biriktirilmagan"}</b></div>
                      <div>🗓 Vaqt: <b className="text-slate-200">{g.schedule?.time || "18:00"}</b> ({g.schedule?.days?.join(", ") || "Dush/Chor/Juma"})</div>
                      <div>👥 Sig'im: <b className="text-emerald-400">{g.active_students_count || 0}</b> / {g.max_students} o'quvchi</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 2. KURSLAR BO'LIMI */}
        {activeTab === "courses" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-black text-white">Mavjud Kurslar ({courses.length})</h2>
              <button
                onClick={handleOpenCreateCourse}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition active:scale-95 flex items-center gap-1.5"
              >
                <span>➕</span>
                <span>Yangi Kurs Qo'shish</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {courses.map((c) => (
                <div
                  key={c.id}
                  className="glass-panel rounded-3xl p-5 border border-slate-800 hover:border-indigo-500/40 transition-all shadow-xl space-y-3 relative"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-black px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase">
                      {c.type} • {c.level}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${c.is_active ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-red-500/20 text-red-300"}`}>
                      {c.is_active ? "Faol" : "Nofaol"}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-black text-base text-white">{c.title_uz || "Kurs"}</h3>
                    <p className="text-xs text-slate-400 line-clamp-2 mt-0.5">
                      {c.description_uz || "Tavsif berilmagan."}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-900/80 rounded-2xl border border-slate-800 text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400 font-semibold">Oylik narx:</span>
                      <span className="font-black text-emerald-400">{(c.price || 0).toLocaleString()} so'm</span>
                    </div>
                    {c.price_per_lesson && (
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-500">1 dars narxi (Refund):</span>
                        <span className="text-slate-300 font-bold">{c.price_per_lesson.toLocaleString()} so'm</span>
                      </div>
                    )}
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-500">Davomiyligi:</span>
                      <span className="text-slate-300 font-bold">{c.duration_months} oy ({c.lessons_per_week} kun/hafta)</span>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-1">
                    <button
                      onClick={() => handleOpenEditCourse(c)}
                      className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-xl border border-slate-700 transition"
                    >
                      ✏️ Tahrirlash
                    </button>
                    <button
                      onClick={() => handleToggleCourse(c.id)}
                      className={`px-3 py-2 rounded-xl text-xs font-bold border transition ${
                        c.is_active
                          ? "bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30"
                          : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      }`}
                    >
                      {c.is_active ? "O'chirish" : "Yoqish"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. GURUHLAR BO'LIMI */}
        {activeTab === "groups" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-black text-white">Guruhlar Ro'yxati ({groups.length})</h2>
              <button
                onClick={handleOpenCreateGroup}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition active:scale-95 flex items-center gap-1.5"
              >
                <span>➕</span>
                <span>Yangi Guruh Ochish</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map((g) => (
                <div
                  key={g.id}
                  className="glass-panel rounded-3xl p-5 border border-slate-800 hover:border-indigo-500/40 transition-all shadow-xl space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-black text-sm text-white">{g.name}</h3>
                    <span className="text-[10px] font-black px-2 py-0.5 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {g.course?.type || "General"} • {g.course?.level || "B1"}
                    </span>
                  </div>

                    <div className="text-xs text-slate-400 space-y-1.5">
                      <div>👨‍🏫 Ustoz: <b className="text-slate-200">{g.teacher?.full_name || g.teacher_name || "Biriktirilmagan"}</b></div>
                      <div>📍 Xona: <b className="text-slate-200">{g.room || "1-xona"}</b></div>
                      <div>🗓 Dars kunlari: <b className="text-slate-200">{Array.isArray(g.schedule) ? g.schedule.map((item) => typeof item === "object" ? item.day : item).join(", ") : (g.schedule?.days?.join(", ") || "Dush-Chor-Juma")}</b></div>
                      <div>⏰ Vaqt: <b className="text-indigo-300 font-bold">{Array.isArray(g.schedule) && g.schedule.length > 0 ? g.schedule[0]?.time : (g.schedule?.time || "18:00")}</b></div>
                      <div>👥 Sig'im: <b className="text-emerald-400">{g.enrolled_students ?? g.active_students_count ?? 0}</b> / {g.max_students} o'quvchi</div>
                      {g.group_chat_link && (
                        <div>
                          🔗 Chati: <a href={g.group_chat_link} target="_blank" rel="noreferrer" className="text-indigo-400 font-bold hover:underline">Guruh havolasi ↗</a>
                        </div>
                      )}
                    </div>

                  <div className="pt-2 border-t border-slate-800 flex gap-2">
                    <button
                      onClick={() => handleOpenEditGroup(g)}
                      className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-xl border border-slate-700 transition"
                    >
                      ✏️ Tahrirlash
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3.1. MENING DARSLARIM (USTOZ KABINETI EMBEDDED) */}
        {activeTab === "my_classes" && (
          <div className="space-y-4">
            <TeacherDashboard embedded={true} onSwitchMode={onSwitchMode} />
          </div>
        )}

        {/* 4. O'QITUVCHILAR BO'LIMI */}
        {activeTab === "teachers" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <h2 className="text-base font-black text-white">Barcha O'qituvchilar ({teachers.length})</h2>

              <button
                onClick={handleOpenCreateTeacher}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/25 transition active:scale-95 flex items-center gap-1.5"
              >
                <span>➕</span>
                <span>Yangi O'qituvchi Qo'shish</span>
              </button>
            </div>

            <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/90 text-slate-400 font-extrabold uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">O'qituvchi</th>
                      <th className="p-3.5">Telegram ID</th>
                      <th className="p-3.5">Telefon</th>
                      <th className="p-3.5">Biriktirilgan Guruhlar</th>
                      <th className="p-3.5 text-right">Harakat</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {teachers.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="p-8 text-center text-slate-500 font-medium">
                          Hozircha o'qituvchilar qo'shilmagan. Yuqoridagi «➕ Yangi O'qituvchi Qo'shish» tugmasi orqali qo'shing.
                        </td>
                      </tr>
                    ) : (
                      teachers.map((t) => (
                        <tr key={t.id} className="hover:bg-slate-800/40 transition">
                          <td className="p-3.5 font-bold text-white flex items-center gap-2">
                            <span className="w-7 h-7 rounded-lg bg-purple-600/20 text-purple-300 font-black flex items-center justify-center text-[10px]">
                              👨‍🏫
                            </span>
                            <div>
                              <div>{t.full_name}</div>
                              <div className="text-[10px] text-slate-400 font-normal">
                                {t.username ? `@${t.username}` : "username yo'q"}
                              </div>
                            </div>
                          </td>
                          <td className="p-3.5 text-slate-400 font-mono font-bold"><code>{t.id}</code></td>
                          <td className="p-3.5 text-slate-300 font-semibold">{t.phone || "—"}</td>
                          <td className="p-3.5">
                            {t.groups && t.groups.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {t.groups.map((g) => (
                                  <span key={g.id} className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold">
                                    {g.name}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-500 italic text-[11px]">Guruh biriktirilmagan</span>
                            )}
                          </td>
                          <td className="p-3.5 text-right">
                            <button
                              onClick={() => handleDeleteTeacher(t.id, t.full_name)}
                              className="px-2.5 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/30 rounded-lg text-[10px] font-bold transition active:scale-95"
                              title="Vazifasidan ozod qilish"
                            >
                              🗑 O'chirish
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 4.1. ADMINLAR BO'LIMI */}
        {activeTab === "admins" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <h2 className="text-base font-black text-white">Barcha Adminlar ({admins.length})</h2>

              <button
                onClick={handleOpenCreateAdmin}
                className="px-4 py-2 bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/25 transition active:scale-95 flex items-center gap-1.5"
              >
                <span>➕</span>
                <span>Yangi Admin Qo'shish</span>
              </button>
            </div>

            <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/90 text-slate-400 font-extrabold uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">Admin</th>
                      <th className="p-3.5">Telegram ID</th>
                      <th className="p-3.5">Telefon</th>
                      <th className="p-3.5">Roli</th>
                      <th className="p-3.5">Qo'shilgan</th>
                      <th className="p-3.5 text-right">Harakat</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {admins.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-slate-500 font-medium">
                          Hozircha adminlar qo'shilmagan. Yuqoridagi «➕ Yangi Admin Qo'shish» tugmasi orqali qo'shing.
                        </td>
                      </tr>
                    ) : (
                      admins.map((a) => (
                        <tr key={a.id} className="hover:bg-slate-800/40 transition">
                          <td className="p-3.5 font-bold text-white flex items-center gap-2">
                            <span className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-300 font-black flex items-center justify-center text-[10px]">
                              👑
                            </span>
                            <div>
                              <div>{a.full_name}</div>
                              <div className="text-[10px] text-slate-400 font-normal">
                                {a.username ? `@${a.username}` : "username yo'q"}
                              </div>
                            </div>
                          </td>
                          <td className="p-3.5 text-slate-400 font-mono font-bold"><code>{a.id}</code></td>
                          <td className="p-3.5 text-slate-300 font-semibold">{a.phone || "—"}</td>
                          <td className="p-3.5">
                            <span className="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-black uppercase">
                              {a.role}
                            </span>
                          </td>
                          <td className="p-3.5 text-slate-400 text-[11px] font-semibold">
                            {a.created_at || "—"}
                          </td>
                          <td className="p-3.5 text-right">
                            <button
                              onClick={() => handleDeleteAdmin(a.id, a.full_name)}
                              className="px-2.5 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/30 rounded-lg text-[10px] font-bold transition active:scale-95"
                              title="Admin huquqini olib tashlash"
                            >
                              🗑 O'chirish
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 5. O'QUVCHILAR BO'LIMI */}
        {activeTab === "students" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <h2 className="text-base font-black text-white">Talabalar ({students.length})</h2>
              
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <input
                  type="text"
                  placeholder="Qidiruv (ism, telefon)..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full sm:w-64 px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-semibold"
                />
                <a
                  href="/api/admin/export/students-csv"
                  download
                  className="px-3 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-xl text-xs font-black transition active:scale-95 shrink-0 flex items-center gap-1"
                >
                  <span>📥</span>
                  <span>Excel (.CSV)</span>
                </a>
              </div>
            </div>

            <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/90 text-slate-400 font-extrabold uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">O'quvchi</th>
                      <th className="p-3.5">Telefon</th>
                      <th className="p-3.5">Guruh / Kurs</th>
                      <th className="p-3.5">Daraja</th>
                      <th className="p-3.5">Ro'yxatdan o'tgan</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredStudents.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5 font-bold text-white flex items-center gap-2">
                          <span className="w-7 h-7 rounded-lg bg-indigo-600/20 text-indigo-300 font-black flex items-center justify-center text-[10px]">
                            {s.full_name?.charAt(0) || "U"}
                          </span>
                          <div>
                            <div>{s.full_name || "Noma'lum"}</div>
                            <div className="text-[10px] text-slate-400 font-normal">@{s.username || "no_user"}</div>
                          </div>
                        </td>
                        <td className="p-3.5 text-slate-300 font-semibold">{s.phone || "—"}</td>
                        <td className="p-3.5 text-slate-300 font-semibold">
                          {s.enrollments && s.enrollments.length > 0
                            ? s.enrollments.map((e) => e.group?.name).join(", ")
                            : <span className="text-slate-500 italic">Yozilmagan</span>}
                        </td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-black">
                            {s.level || "A1"}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-400 text-[11px]">
                          {s.created_at ? new Date(s.created_at).toLocaleDateString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 5. TO'LOVLAR BO'LIMI */}
        {activeTab === "payments" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <h2 className="text-base font-black text-white">Barcha To'lovlar ({payments.length})</h2>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <select
                  value={paymentFilter}
                  onChange={(e) => setPaymentFilter(e.target.value)}
                  className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs font-bold text-slate-200 outline-none focus:border-indigo-500"
                >
                  <option value="all">Barcha holatlar</option>
                  <option value="pending">⏳ Kutilmoqda</option>
                  <option value="paid">✅ Tasdiqlangan</option>
                  <option value="refunded">💰 Qaytarilgan</option>
                  <option value="failed">❌ Rad etilgan</option>
                </select>

                <a
                  href="/api/admin/export/payments-csv"
                  download
                  className="px-3 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-xl text-xs font-black transition active:scale-95 shrink-0 flex items-center gap-1"
                >
                  <span>📥</span>
                  <span>Excel (.CSV)</span>
                </a>
              </div>
            </div>

            <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/90 text-slate-400 font-extrabold uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">ID</th>
                      <th className="p-3.5">Talaba</th>
                      <th className="p-3.5">Guruh</th>
                      <th className="p-3.5">Summa</th>
                      <th className="p-3.5">Usul</th>
                      <th className="p-3.5">Holati</th>
                      <th className="p-3.5">Sana</th>
                      <th className="p-3.5 text-right">Harakat</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredPayments.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5 text-slate-400 font-black">#{p.id}</td>
                        <td className="p-3.5 font-bold text-white">
                          {p.student?.full_name || `User #${p.student_id}`}
                        </td>
                        <td className="p-3.5 text-slate-300 font-semibold">{p.group?.name || "—"}</td>
                        <td className="p-3.5 font-black text-emerald-400">
                          {(p.amount || 0).toLocaleString()} so'm
                        </td>
                        <td className="p-3.5">
                          <span className="uppercase text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            {p.method || p.provider}
                          </span>
                        </td>
                        <td className="p-3.5">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-black border ${
                              p.status === "paid" || p.status === "confirmed"
                                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                                : p.status === "pending"
                                ? "bg-amber-500/20 text-amber-300 border-amber-500/30 animate-pulse"
                                : p.status === "refunded"
                                ? "bg-purple-500/20 text-purple-300 border-purple-500/30"
                                : "bg-red-500/20 text-red-300 border-red-500/30"
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-400 text-[11px]">
                          {p.created_at ? new Date(p.created_at).toLocaleDateString() : "—"}
                        </td>
                        <td className="p-3.5 text-right">
                          {p.status === "pending" && (
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => handleApprovePayment(p.id)}
                                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-black text-[11px] rounded-lg shadow-md transition active:scale-95"
                              >
                                ✅ Tasdiqlash
                              </button>
                              <button
                                onClick={() => handleRejectPayment(p.id)}
                                className="px-2.5 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-300 font-black text-[11px] rounded-lg border border-red-500/30 transition active:scale-95"
                              >
                                ✕ Rad etish
                              </button>
                            </div>
                          )}
                          {(p.status === "confirmed" || p.status === "paid") && (
                            <div className="flex items-center justify-end">
                              <button
                                onClick={() => handleRefundPayment(p.id)}
                                className="px-2.5 py-1 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 font-bold text-[11px] rounded-lg border border-purple-500/30 transition active:scale-95 flex items-center gap-1"
                                title="Pulni qaytarish va o'quvchini guruhdan chiqarish"
                              >
                                <span>💰</span>
                                <span>Refund</span>
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 6. BROADCAST BO'LIMI */}
        {activeTab === "broadcast" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 shadow-2xl space-y-5">
              <div>
                <h2 className="text-base font-black text-white flex items-center gap-2">
                  📢 Ommaviy Xabarnoma (Broadcast)
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Barcha yoki tanlangan auditoriyaga to'g'ridan-to'g'ri Telegram orqali xabar yuborish.
                </p>
              </div>

              {/* Auditoriya Tanlash */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">
                  👥 1. Auditoriyani tanlang:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    { id: "all", label: "👥 Barchaga", desc: "Hammasi" },
                    { id: "student", label: "🎓 O'quvchilarga", desc: "Faqat talabalar" },
                    { id: "teacher", label: "👨‍🏫 O'qituvchilarga", desc: "Faqat ustozlar" },
                    { id: "IELTS", label: "🎯 IELTS guruhlari", desc: "IELTS talabalari" },
                    { id: "CEFR", label: "🎯 CEFR guruhlari", desc: "CEFR talabalari" },
                  ].map((target) => {
                    const isSelected = broadcastRole === target.id;
                    return (
                      <button
                        key={target.id}
                        type="button"
                        onClick={() => setBroadcastRole(target.id)}
                        className={`p-3 rounded-2xl border text-left transition-all active:scale-95 ${
                          isSelected
                            ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30"
                            : "bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800"
                        }`}
                      >
                        <div className="font-black text-xs">{target.label}</div>
                        <div className={`text-[10px] mt-0.5 ${isSelected ? "text-indigo-200" : "text-slate-400"}`}>
                          {target.desc}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tezkor Shablonlar */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">
                  ⚡️ 2. Tayyor shablon tugmalari:
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    {
                      label: "📢 Yangi guruh qabuli",
                      text: "🔥 <b>Yangi guruhlarimizga qabul boshlandi!</b>\n\nIngliz tilini tez va samarali o'rganishni istaysizmi? IELTS va CEFR guruhlarimizga hoziroq qo'shiling!\n\nJoylar soni cheklangan!",
                      btnText: "📝 Free Darsga Yozilish",
                      btnUrl: "https://t.me/alphacenterbot",
                    },
                    {
                      label: "🎉 Bayram tabrigi",
                      text: "🎉 <b>Aziz o'quvchilar va ustozlar!</b>\n\nSizlarni bayram bilan samimiy muborakbod etamiz! Sizga sihat-salomatlik, ulkan muvaffaqiyatlar va yangi yutuqlar tilaymiz! 🌟",
                      btnText: "",
                      btnUrl: "",
                    },
                    {
                      label: "⚠️ To'lov eslatmasi",
                      text: "🔔 <b>Hurmatli o'quvchi!</b>\n\nKeyingi oylik darslar to'lovini amalga oshirish muddati yaqinlashmoqda. Darslaringiz uzluksiz davom etishi uchun to'lovni o'z vaqtida amalga oshirishingizni so'raymiz.\n\nTo'lov uchun bot menyusidagi «💳 To'lov» bo'limidan foydalaning.",
                      btnText: "💳 To'lov Qilish",
                      btnUrl: "https://t.me/alphacenterbot",
                    },
                    {
                      label: "🎯 Bepul sinov darsi",
                      text: "🎁 <b>Ingliz tili darajangizni bepul tekshiring!</b>\n\nBotimiz orqali test topshiring va o'zingizga mos guruhda 1 ta BEPUL sinov darsida qatnashing!",
                      btnText: "🎯 Testni Boshlash",
                      btnUrl: "https://t.me/alphacenterbot",
                    },
                  ].map((tpl, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        setBroadcastText(tpl.text);
                        if (tpl.btnText && tpl.btnUrl) {
                          setHasBroadcastBtn(true);
                          setBroadcastBtnText(tpl.btnText);
                          setBroadcastBtnUrl(tpl.btnUrl);
                        }
                      }}
                      className="px-3 py-1.5 bg-slate-900 hover:bg-indigo-600/20 hover:text-indigo-300 border border-slate-700/80 rounded-xl text-xs font-bold text-slate-300 transition active:scale-95"
                    >
                      {tpl.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Xabar Matni Formasi */}
              <form onSubmit={handleSendBroadcast} className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-xs font-bold text-slate-300">
                      ✍️ 3. Xabar matni (HTML):
                    </label>
                    <span className="text-[10px] text-slate-500 font-mono">
                      &lt;b&gt;, &lt;i&gt;, &lt;code&gt;
                    </span>
                  </div>
                  <textarea
                    rows={5}
                    value={broadcastText}
                    onChange={(e) => setBroadcastText(e.target.value)}
                    placeholder="Xabaringizni bu yerga yozing..."
                    className="w-full p-3.5 bg-slate-900 border border-slate-700 rounded-2xl text-xs font-medium text-slate-100 outline-none focus:border-indigo-500 transition"
                  ></textarea>
                </div>

                {/* Inline Havola Tugmasi */}
                <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-2xl space-y-3">
                  <label className="text-xs font-black text-slate-200 flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={hasBroadcastBtn}
                      onChange={(e) => setHasBroadcastBtn(e.target.checked)}
                      className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-700"
                    />
                    🔗 Xabar ostiga tugma qo'shish (Inline Button)
                  </label>

                  {hasBroadcastBtn && (
                    <div className="space-y-3 pt-2 border-t border-slate-800">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[11px] font-bold text-slate-400 mb-1">
                            Tugma matni:
                          </label>
                          <input
                            type="text"
                            placeholder="Masalan: 🌐 Batafsil"
                            value={broadcastBtnText}
                            onChange={(e) => setBroadcastBtnText(e.target.value)}
                            className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs font-bold text-white outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-bold text-slate-400 mb-1">
                            Havola URL:
                          </label>
                          <input
                            type="text"
                            placeholder="https://t.me/alphacenter"
                            value={broadcastBtnUrl}
                            onChange={(e) => setBroadcastBtnUrl(e.target.value)}
                            className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs font-bold text-white outline-none focus:border-indigo-500"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Telegram Preview */}
                {broadcastText.trim() && (
                  <div className="p-4 bg-slate-950 rounded-2xl text-white space-y-2 border border-slate-800 shadow-inner">
                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-wider">
                      📱 Telegram Ko'rinishi (Preview):
                    </div>
                    <div
                      className="text-xs leading-relaxed break-words text-slate-200"
                      dangerouslySetInnerHTML={{
                        __html: broadcastText.replace(/\n/g, "<br/>"),
                      }}
                    />
                    {hasBroadcastBtn && broadcastBtnText.trim() && (
                      <div className="pt-2">
                        <div className="w-full py-2 bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-center font-black text-xs rounded-xl">
                          🔗 {broadcastBtnText}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Yuborish Tugmasi */}
                <button
                  type="submit"
                  disabled={broadcasting || !broadcastText.trim()}
                  className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-black text-xs rounded-2xl transition shadow-xl shadow-indigo-600/25 active:scale-[0.99] disabled:opacity-40 disabled:pointer-events-none flex items-center justify-center gap-2"
                >
                  {broadcasting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Yuborilmoqda...
                    </>
                  ) : (
                    <>🚀 Xabarni Yuborish ({broadcastRole})</>
                  )}
                </button>

                {broadcastResult && (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 p-4 rounded-2xl text-xs font-bold text-center">
                    ✅ {broadcastResult.message}
                  </div>
                )}
              </form>
            </div>
          </div>
        )}

        {/* 7. MARKAZ SOZLAMALARI BO'LIMI */}
        {activeTab === "settings" && (
          <div className="max-w-2xl mx-auto space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-black text-white">
                  {t.settings?.title || "⚙️ Markaz Ma'lumotlari va Sozlamalari"}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t.settings?.desc || "Ushbu ma'lumotlar botning «📞 Bog'lanish» va «Xush kelibsiz» bo'limlarida barcha o'quvchilarga dinamik ko'rsatiladi."}
                </p>
              </div>
            </div>

            <form onSubmit={handleSaveCenterSettings} className="glass-panel rounded-3xl p-6 border border-slate-800 shadow-2xl space-y-4">
              {settingsSuccess && (
                <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs font-bold flex items-center gap-2">
                  <span>✅</span>
                  <span>{t.settings?.savedAlert || "Markaz sozlamalari muvaffaqiyatli saqlandi! Botda darhol yangilandi."}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  {t.settings?.phoneLabel || "☎️ Markaz Telefon Raqami:"}
                </label>
                <input
                  type="text"
                  value={centerSettings.contact_phone}
                  onChange={(e) => setCenterSettings({ ...centerSettings, contact_phone: e.target.value })}
                  placeholder="+998 90 123 45 67"
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-sm font-semibold"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  {t.settings?.usernameLabel || "✍️ Administrator Telegram Username:"}
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-2.5 text-slate-400 font-bold">@</span>
                  <input
                    type="text"
                    value={centerSettings.contact_username.replace(/^@/, "")}
                    onChange={(e) => setCenterSettings({ ...centerSettings, contact_username: e.target.value.replace(/^@/, "") })}
                    placeholder="english_center_admin"
                    required
                    className="w-full pl-8 pr-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-sm font-semibold"
                  />
                </div>
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-800">
                <label className="block text-xs font-black text-slate-200">
                  {t.settings?.addressesTitle || "📍 O'quv Markazi Manzillari:"}
                </label>
                <div>
                  <span className="block text-[11px] font-bold text-slate-400 mb-1">
                    {t.settings?.addressUz || "O'zbekcha manzil (UZ):"}
                  </span>
                  <input
                    type="text"
                    value={centerSettings.address_uz}
                    onChange={(e) => setCenterSettings({ ...centerSettings, address_uz: e.target.value })}
                    placeholder="Toshkent sh., Amir Temur ko'chasi, 12-uy"
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-xs"
                  />
                </div>
                <div>
                  <span className="block text-[11px] font-bold text-slate-400 mb-1">
                    {t.settings?.addressRu || "Ruscha manzil (RU):"}
                  </span>
                  <input
                    type="text"
                    value={centerSettings.address_ru || ""}
                    onChange={(e) => setCenterSettings({ ...centerSettings, address_ru: e.target.value })}
                    placeholder="г. Ташкент, ул. Амира Темура, д. 12"
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-xs"
                  />
                </div>
                <div>
                  <span className="block text-[11px] font-bold text-slate-400 mb-1">
                    {t.settings?.addressEn || "Inglizcha manzil (EN):"}
                  </span>
                  <input
                    type="text"
                    value={centerSettings.address_en || ""}
                    onChange={(e) => setCenterSettings({ ...centerSettings, address_en: e.target.value })}
                    placeholder="12 Amir Temur street, Tashkent"
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-xs"
                  />
                </div>
              </div>

              {/* WELCOME MESSAGES IN 3 LANGUAGES */}
              <div className="space-y-3 pt-3 border-t border-slate-800">
                <label className="block text-xs font-black text-slate-200">
                  {t.settings?.welcomeTitle || "👋 Bot Xush Kelibsiz Xabari (Welcome Message):"}
                </label>
                <div>
                  <span className="block text-[11px] font-bold text-slate-400 mb-1">
                    {t.settings?.welcomeUz || "O'zbekcha xush kelibsiz xabari (UZ):"}
                  </span>
                  <textarea
                    rows={2}
                    value={centerSettings.welcome_message_uz || ""}
                    onChange={(e) => setCenterSettings({ ...centerSettings, welcome_message_uz: e.target.value })}
                    placeholder="Xush kelibsiz! Alpha English Center rasmiy botiga xush kelibsiz..."
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-xs resize-none"
                  />
                </div>
                <div>
                  <span className="block text-[11px] font-bold text-slate-400 mb-1">
                    {t.settings?.welcomeRu || "Ruscha xush kelibsiz xabari (RU):"}
                  </span>
                  <textarea
                    rows={2}
                    value={centerSettings.welcome_message_ru || ""}
                    onChange={(e) => setCenterSettings({ ...centerSettings, welcome_message_ru: e.target.value })}
                    placeholder="Добро пожаловать в официальный бот Alpha English Center..."
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-xs resize-none"
                  />
                </div>
                <div>
                  <span className="block text-[11px] font-bold text-slate-400 mb-1">
                    {t.settings?.welcomeEn || "Inglizcha xush kelibsiz xabari (EN):"}
                  </span>
                  <textarea
                    rows={2}
                    value={centerSettings.welcome_message_en || ""}
                    onChange={(e) => setCenterSettings({ ...centerSettings, welcome_message_en: e.target.value })}
                    placeholder="Welcome to the official Alpha English Center bot..."
                    className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 text-xs resize-none"
                  />
                </div>
              </div>

              <div className="pt-3">
                <button
                  type="submit"
                  disabled={settingsSaving}
                  className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {settingsSaving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>{t.settings?.savingBtn || "Saqlanmoqda..."}</span>
                    </>
                  ) : (
                    <>
                      <span>💾</span>
                      <span>{t.settings?.saveBtn || "Sozlamalarni Saqlash"}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>

      {/* MODAL: KURS QO'SHISH / TAHRIRLASH */}
      {showCourseModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel border border-slate-700 bg-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl max-h-[90vh] overflow-y-auto space-y-4">
            <h3 className="font-black text-white text-base">
              {editingCourse ? "✏️ Kursni Tahrirlash" : "➕ Yangi Kurs Yaratish"}
            </h3>

            <form onSubmit={handleSaveCourse} className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Kurs Nomi (UZ):</label>
                <input
                  type="text"
                  required
                  value={courseForm.title_uz}
                  onChange={(e) => setCourseForm({ ...courseForm, title_uz: e.target.value })}
                  placeholder="Masalan: IELTS Intensive"
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Yo'nalish:</label>
                  <select
                    value={courseForm.type}
                    onChange={(e) => setCourseForm({ ...courseForm, type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                  >
                    <option value="IELTS">IELTS</option>
                    <option value="CEFR">CEFR</option>
                    <option value="General">General English</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Daraja:</label>
                  <select
                    value={courseForm.level}
                    onChange={(e) => setCourseForm({ ...courseForm, level: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                  >
                    {["A1", "A2", "B1", "B2", "C1", "C2"].map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Oylik Narxi (so'm):</label>
                  <input
                    type="number"
                    required
                    value={courseForm.price}
                    onChange={(e) => setCourseForm({ ...courseForm, price: e.target.value })}
                    placeholder="500000"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">1 dars narxi (Refund):</label>
                  <input
                    type="number"
                    value={courseForm.price_per_lesson}
                    onChange={(e) => setCourseForm({ ...courseForm, price_per_lesson: e.target.value })}
                    placeholder="45000"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Tavsif (UZ):</label>
                <textarea
                  rows={3}
                  value={courseForm.description_uz}
                  onChange={(e) => setCourseForm({ ...courseForm, description_uz: e.target.value })}
                  placeholder="Kurs haqida qisqacha ma'lumot..."
                  className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500"
                ></textarea>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCourseModal(false)}
                  className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-black rounded-xl shadow-lg shadow-indigo-600/30 transition"
                >
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: GURUH QO'SHISH / TAHRIRLASH */}
      {showGroupModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel border border-slate-700 bg-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl max-h-[90vh] overflow-y-auto space-y-4">
            <h3 className="font-black text-white text-base">
              {editingGroup ? "✏️ Guruhni Tahrirlash" : "➕ Yangi Guruh Ochish"}
            </h3>

            <form onSubmit={handleSaveGroup} className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Kursni Tanlang:</label>
                <select
                  value={groupForm.course_id}
                  onChange={(e) => setGroupForm({ ...groupForm, course_id: e.target.value })}
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title_uz} ({c.type} • {c.level})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Guruh Nomi:</label>
                <input
                  type="text"
                  required
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                  placeholder="Masalan: IELTS Morning Alpha"
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">O'qituvchi:</label>
                <select
                  value={groupForm.teacher_id}
                  onChange={(e) => setGroupForm({ ...groupForm, teacher_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                >
                  <option value="">Biriktirilmagan</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>{t.full_name}</option>
                  ))}
                </select>
              </div>

              {/* DARS KUNLARI (HAFTA KUNLARI) */}
              <div className="space-y-2 pt-1 pb-1 border-y border-slate-800/80">
                <div className="flex items-center justify-between">
                  <label className="block text-[11px] font-bold text-slate-300">
                    🗓 Dars Kunlari:
                  </label>
                  <span className="text-[10px] text-indigo-400 font-bold bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
                    {groupForm.schedule_days.length} ta kun tanlandi
                  </span>
                </div>

                {/* Tezkor andozalar (Presets) */}
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => handleSetPresetDays(["Monday", "Wednesday", "Friday"])}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition active:scale-95 ${
                      JSON.stringify((groupForm.schedule_days || []).slice().sort()) === JSON.stringify(["Friday", "Monday", "Wednesday"].sort())
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                        : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                    }`}
                  >
                    Toq kunlar (Dush-Chor-Jum)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSetPresetDays(["Tuesday", "Thursday", "Saturday"])}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition active:scale-95 ${
                      JSON.stringify((groupForm.schedule_days || []).slice().sort()) === JSON.stringify(["Saturday", "Thursday", "Tuesday"].sort())
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                        : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                    }`}
                  >
                    Juft kunlar (Sesh-Pay-Shan)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSetPresetDays(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])}
                    className="px-2.5 py-1 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-lg text-[10px] font-bold transition active:scale-95"
                  >
                    Har kuni (Dush-Shan)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSetPresetDays(["Saturday", "Sunday"])}
                    className="px-2.5 py-1 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-lg text-[10px] font-bold transition active:scale-95"
                  >
                    Dam olish (Shan-Yak)
                  </button>
                </div>

                {/* Kunlarni alohida tanlash chips */}
                <div className="grid grid-cols-7 gap-1 pt-1">
                  {WEEK_DAYS.map((wd) => {
                    const isSelected = (groupForm.schedule_days || []).includes(wd.id);
                    return (
                      <button
                        key={wd.id}
                        type="button"
                        onClick={() => handleToggleDay(wd.id)}
                        className={`py-2 px-1 rounded-xl text-[11px] font-black text-center transition flex flex-col items-center justify-center gap-0.5 border active:scale-95 ${
                          isSelected
                            ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                        }`}
                        title={wd.full}
                      >
                        <span>{wd.label}</span>
                        <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? "bg-emerald-400 animate-pulse" : "bg-transparent"}`}></span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Dars Boshlanish Vaqti:</label>
                  <input
                    type="time"
                    value={groupForm.schedule_time}
                    onChange={(e) => setGroupForm({ ...groupForm, schedule_time: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Sig'im (o'quvchilar):</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={groupForm.max_students}
                    onChange={(e) => setGroupForm({ ...groupForm, max_students: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">🔗 Guruh Telegram Chat Havolasi (Link):</label>
                <input
                  type="url"
                  value={groupForm.group_chat_link}
                  onChange={(e) => setGroupForm({ ...groupForm, group_chat_link: e.target.value })}
                  placeholder="https://t.me/+AbCdEfGh123..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 font-medium"
                />
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Ushbu havola talabaning profilida («👤 Profilim») avtomatik ko'rinadi.
                </p>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">🎥 Zoom / Online Dars Havolasi (Ixtiyoriy):</label>
                <input
                  type="url"
                  value={groupForm.zoom_link}
                  onChange={(e) => setGroupForm({ ...groupForm, zoom_link: e.target.value })}
                  placeholder="https://us02web.zoom.us/j/..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGroupModal(false)}
                  className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-black rounded-xl shadow-lg shadow-indigo-600/30 transition"
                >
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* MODAL: O'QITUVCHI QO'SHISH */}
      {showTeacherModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel border border-slate-700 bg-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="font-black text-white text-base">➕ Yangi O'qituvchi Qo'shish</h3>
            <p className="text-xs text-slate-400">
              O'qituvchining Telegram ID si yoki raqamini kiritib, unga O'qituvchi boshqaruv huquqini bering.
            </p>

            <form onSubmit={handleSaveTeacher} className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Telegram ID:*</label>
                <input
                  type="number"
                  required
                  value={teacherForm.telegram_id}
                  onChange={(e) => setTeacherForm({ ...teacherForm, telegram_id: e.target.value })}
                  placeholder="Masalan: 123456789"
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-mono font-bold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Ism va Familiya:*</label>
                <input
                  type="text"
                  required
                  value={teacherForm.full_name}
                  onChange={(e) => setTeacherForm({ ...teacherForm, full_name: e.target.value })}
                  placeholder="Masalan: Jasur Abdullayev"
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Telefon Raqam:</label>
                  <input
                    type="text"
                    value={teacherForm.phone}
                    onChange={(e) => setTeacherForm({ ...teacherForm, phone: e.target.value })}
                    placeholder="+998901234567"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Username:</label>
                  <input
                    type="text"
                    value={teacherForm.username}
                    onChange={(e) => setTeacherForm({ ...teacherForm, username: e.target.value })}
                    placeholder="jasur_teacher"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowTeacherModal(false)}
                  className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-black rounded-xl shadow-lg shadow-indigo-600/30 transition"
                >
                  Biriktirish
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* MODAL: ADMIN QO'SHISH */}
      {showAdminModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel border border-amber-500/40 bg-slate-900 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="font-black text-white text-base flex items-center gap-2">
              <span className="text-xl">👑</span>
              <span>Yangi Admin Tayinlash</span>
            </h3>
            <p className="text-xs text-slate-400">
              Foydalanuvchining Telegram ID sini kiritib, unga to'liq Boshqaruvchi (Admin) huquqini bering.
            </p>

            <form onSubmit={handleSaveAdmin} className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Telegram ID:*</label>
                <input
                  type="number"
                  required
                  value={adminForm.telegram_id}
                  onChange={(e) => setAdminForm({ ...adminForm, telegram_id: e.target.value })}
                  placeholder="Masalan: 123456789"
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-mono font-bold outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">Ism va Familiya:*</label>
                <input
                  type="text"
                  required
                  value={adminForm.full_name}
                  onChange={(e) => setAdminForm({ ...adminForm, full_name: e.target.value })}
                  placeholder="Masalan: Jasur Karimov"
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-bold outline-none focus:border-amber-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Telefon Raqam:</label>
                  <input
                    type="text"
                    value={adminForm.phone}
                    onChange={(e) => setAdminForm({ ...adminForm, phone: e.target.value })}
                    placeholder="+998901234567"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 mb-1">Username:</label>
                  <input
                    type="text"
                    value={adminForm.username}
                    onChange={(e) => setAdminForm({ ...adminForm, username: e.target.value })}
                    placeholder="jasur_admin"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAdminModal(false)}
                  className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white font-black rounded-xl shadow-lg shadow-indigo-600/30 transition"
                >
                  Admin Tayinlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
