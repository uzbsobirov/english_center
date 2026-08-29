import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { getTelegramLanguage, setTelegramLanguage } from "../lib/telegram";

export default function AdminDashboard({ onSwitchMode }) {
  const [lang, setLang] = useState(getTelegramLanguage);
  const [activeTab, setActiveTab] = useState("dashboard"); // dashboard, courses, groups, students, payments, broadcast
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Data states
  const [stats, setStats] = useState(null);
  const [courses, setCourses] = useState([]);
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
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
    zoom_link: "",
  });

  // Broadcast state
  const [broadcastText, setBroadcastText] = useState("");
  const [broadcastRole, setBroadcastRole] = useState("all");
  const [broadcastLevel, setBroadcastLevel] = useState("");
  const [broadcasting, setBroadcasting] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState(null);

  const fetchDashboardData = () => {
    setLoading(true);
    setError(null);

    Promise.all([
      apiClient.get("/api/admin/dashboard").then((r) => setStats(r.data)),
      apiClient.get("/api/admin/courses").then((r) => setCourses(r.data)),
      apiClient.get("/api/admin/groups").then((r) => setGroups(r.data)),
      apiClient.get("/api/admin/teachers").then((r) => setTeachers(r.data)),
      apiClient.get("/api/admin/students").then((r) => setStudents(r.data)),
      apiClient.get("/api/admin/payments").then((r) => setPayments(r.data)),
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
      zoom_link: "",
    });
    setShowGroupModal(true);
  };

  const handleOpenEditGroup = (g) => {
    setEditingGroup(g);
    const days = Array.isArray(g.schedule) ? g.schedule.map((s) => s.day || s) : ["Monday", "Wednesday", "Friday"];
    const time = Array.isArray(g.schedule) && g.schedule[0]?.time ? g.schedule[0].time : "18:00";

    setGroupForm({
      course_id: g.course_id,
      name: g.name,
      teacher_id: g.teacher_id || "",
      schedule_days: days,
      schedule_time: time,
      room: g.room || "1-xona",
      max_students: g.max_students || 12,
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
      ...groupForm,
      course_id: parseInt(groupForm.course_id, 10),
      teacher_id: groupForm.teacher_id ? parseInt(groupForm.teacher_id, 10) : null,
      max_students: parseInt(groupForm.max_students, 10),
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

  const handleToggleGroup = async (groupId) => {
    try {
      await apiClient.delete(`/api/admin/groups/${groupId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    }
  };

  // Payment Handlers
  const handleApprovePayment = async (paymentId) => {
    try {
      await apiClient.post(`/api/admin/payments/${paymentId}/approve`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Xatolik yuz berdi");
    }
  };

  const handleRejectPayment = async (paymentId) => {
    if (!window.confirm("Haqiqatan ham bu to'lovni rad etmoqchimisiz?")) return;
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
        target_role: broadcastRole === "all" ? null : broadcastRole,
        level: broadcastLevel || null,
      });
      setBroadcastResult(res.data);
      setBroadcastText("");
    } catch (err) {
      alert(err.response?.data?.detail || "Xabar yuborishda xatolik");
    } finally {
      setBroadcasting(false);
    }
  };

  // Filtered payments
  const filteredPayments = payments.filter((p) => {
    if (paymentFilter !== "all" && p.status !== paymentFilter) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        p.student_name.toLowerCase().includes(term) ||
        p.group_name.toLowerCase().includes(term)
      );
    }
    return true;
  });

  // Filtered students
  const filteredStudents = students.filter((s) => {
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        s.full_name.toLowerCase().includes(term) ||
        (s.username && s.username.toLowerCase().includes(term)) ||
        (s.phone && s.phone.includes(term)) ||
        s.group_name.toLowerCase().includes(term)
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800 pb-20">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">👑</span>
            <div>
              <h1 className="font-extrabold text-slate-900 text-lg leading-tight">
                Alpha Admin Dashboard
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                O'quv markazini boshqarish tizimi
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onSwitchMode && (
              <button
                onClick={() => onSwitchMode("teacher")}
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold rounded-xl transition"
              >
                🛠 Test Builder
              </button>
            )}
            <button
              onClick={fetchDashboardData}
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-50 rounded-xl transition"
              title="Yangilash"
            >
              🔄
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-6xl mx-auto px-4 flex gap-1 overflow-x-auto no-scrollbar border-t border-slate-100 text-xs font-bold">
          {[
            { id: "dashboard", label: "📊 Asosiy", badge: null },
            { id: "courses", label: "📚 Kurslar", badge: courses.length },
            { id: "groups", label: "👥 Guruhlar", badge: groups.length },
            { id: "students", label: "🎓 O'quvchilar", badge: students.length },
            {
              id: "payments",
              label: "💳 To'lovlar",
              badge: stats?.pending_payments ? `${stats.pending_payments} kutilmoqda` : null,
              badgeColor: "bg-amber-100 text-amber-800",
            },
            { id: "broadcast", label: "📢 Broadcast", badge: null },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-3.5 whitespace-nowrap border-b-2 flex items-center gap-1.5 transition ${
                  isActive
                    ? "border-blue-600 text-blue-600 bg-blue-50/50"
                    : "border-transparent text-slate-600 hover:text-slate-900"
                }`}
              >
                <span>{tab.label}</span>
                {tab.badge && (
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                      tab.badgeColor || "bg-slate-200 text-slate-700"
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

      {/* Main Content Area */}
      <main className="max-w-6xl mx-auto p-4 space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-xs flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button onClick={fetchDashboardData} className="underline font-bold">
              Qayta urinish
            </button>
          </div>
        )}

        {/* 1. ASOSIY DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-2xl mb-1 block">👥</span>
                <div className="text-xl font-black text-slate-800">
                  {stats?.total_students ?? 0}
                </div>
                <div className="text-xs text-slate-500 font-semibold">O'quvchilar</div>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-2xl mb-1 block">📚</span>
                <div className="text-xl font-black text-slate-800">
                  {courses.length}
                </div>
                <div className="text-xs text-slate-500 font-semibold">Kurslar</div>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-2xl mb-1 block">🏢</span>
                <div className="text-xl font-black text-slate-800">
                  {stats?.active_groups ?? 0}
                </div>
                <div className="text-xs text-slate-500 font-semibold">Guruhlar</div>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-2xl mb-1 block">👨‍🏫</span>
                <div className="text-xl font-black text-slate-800">
                  {stats?.total_teachers ?? 0}
                </div>
                <div className="text-xs text-slate-500 font-semibold">O'qituvchilar</div>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                <span className="text-2xl mb-1 block">⏳</span>
                <div className="text-xl font-black text-amber-600">
                  {stats?.pending_payments ?? 0}
                </div>
                <div className="text-xs text-slate-500 font-semibold">Kutilayotgan To'lov</div>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm col-span-2 sm:col-span-1">
                <span className="text-2xl mb-1 block">💰</span>
                <div className="text-base font-black text-emerald-600 truncate">
                  {(stats?.total_revenue ?? 0).toLocaleString()} so'm
                </div>
                <div className="text-xs text-slate-500 font-semibold">Jami Tushum</div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-3xl p-6 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-black mb-1">Tezkor Kurs va Guruh Qo'shish</h3>
                <p className="text-xs text-blue-100 max-w-md leading-relaxed">
                  Markazda yangi IELTS / CEFR kursi oching yoki yangi dars guruhini bir zumda shakllantiring.
                </p>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <button
                  onClick={handleOpenCreateCourse}
                  className="flex-1 sm:flex-none px-4 py-2.5 bg-white text-blue-700 font-extrabold text-xs rounded-xl shadow hover:bg-blue-50 transition active:scale-95"
                >
                  ➕ Yangi Kurs
                </button>
                <button
                  onClick={handleOpenCreateGroup}
                  className="flex-1 sm:flex-none px-4 py-2.5 bg-blue-500/40 border border-white/30 text-white font-extrabold text-xs rounded-xl hover:bg-blue-500/60 transition active:scale-95"
                >
                  ➕ Yangi Guruh
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 2. KURSLAR BO'LIMI */}
        {activeTab === "courses" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-extrabold text-slate-800">
                Barcha Kurslar ({courses.length})
              </h2>
              <button
                onClick={handleOpenCreateCourse}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow flex items-center gap-1.5"
              >
                <span>➕ Yangi Kurs Yaratish</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {courses.map((c) => (
                <div
                  key={c.id}
                  className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-0.5 rounded-lg bg-blue-100 text-blue-700 font-extrabold text-xs">
                        {c.type} • {c.level}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          c.is_active
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {c.is_active ? "Faol" : "Nofaol"}
                      </span>
                    </div>

                    <h3 className="font-extrabold text-slate-900 text-base mb-1">
                      {c.title_uz || c.title?.uz || "Nomsiz kurs"}
                    </h3>
                    <p className="text-xs text-slate-500 mb-3 line-clamp-2">
                      {c.description_uz || c.description?.uz || "Tavsif kiritilmagan"}
                    </p>

                    <div className="bg-slate-50 rounded-xl p-3 space-y-1.5 text-xs text-slate-600 mb-4">
                      <div className="flex justify-between">
                        <span>Kurs narxi:</span>
                        <span className="font-bold text-slate-900">
                          {c.price.toLocaleString()} so'm
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Bir dars narxi (Refund):</span>
                        <span className="font-semibold text-slate-800">
                          {c.price_per_lesson ? c.price_per_lesson.toLocaleString() : "-"} so'm
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Davomiyligi:</span>
                        <span className="font-semibold">
                          {c.duration_months} oy ({c.lessons_per_week} dars/hafta)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Aktiv guruhlar:</span>
                        <span className="font-bold text-blue-600">{c.groups_count} ta guruh</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2 border-t border-slate-100 pt-3">
                    <button
                      onClick={() => handleOpenEditCourse(c)}
                      className="flex-1 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-lg transition"
                    >
                      ✏️ Tahrirlash
                    </button>
                    <button
                      onClick={() => handleToggleCourse(c.id)}
                      className={`px-3 py-1.5 font-bold text-xs rounded-lg transition ${
                        c.is_active
                          ? "bg-red-50 text-red-600 hover:bg-red-100"
                          : "bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                      }`}
                    >
                      {c.is_active ? "O'chirish" : "Faollashtirish"}
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
              <h2 className="text-base font-extrabold text-slate-800">
                Barcha Guruhlar ({groups.length})
              </h2>
              <button
                onClick={handleOpenCreateGroup}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow flex items-center gap-1.5"
              >
                <span>➕ Yangi Guruh Yaratish</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map((g) => {
                const occupancy = Math.round((g.enrolled_students / g.max_students) * 100);
                return (
                  <div
                    key={g.id}
                    className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700">
                          {g.course_title}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            g.is_active
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          {g.is_active ? "Faol" : "Nofaol"}
                        </span>
                      </div>

                      <h3 className="font-extrabold text-slate-900 text-base mb-1">{g.name}</h3>
                      <p className="text-xs text-slate-500 mb-3">
                        👨‍🏫 O'qituvchi: <span className="font-bold text-slate-700">{g.teacher_name}</span>
                      </p>

                      {/* Bandlik progress bari */}
                      <div className="mb-4">
                        <div className="flex justify-between text-xs font-semibold mb-1">
                          <span className="text-slate-500">O'quvchilar sig'imi:</span>
                          <span className="font-bold text-slate-800">
                            {g.enrolled_students} / {g.max_students} ({occupancy}%)
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              occupancy >= 100
                                ? "bg-red-500"
                                : occupancy >= 75
                                ? "bg-amber-500"
                                : "bg-blue-600"
                            }`}
                            style={{ width: `${Math.min(occupancy, 100)}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-2.5 rounded-xl mb-4">
                        <div>
                          📍 Xona / Manzil: <b>{g.room || "Asosiy xona"}</b>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2 border-t border-slate-100 pt-3">
                      <button
                        onClick={() => handleOpenEditGroup(g)}
                        className="flex-1 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-lg transition"
                      >
                        ✏️ Tahrirlash
                      </button>
                      <button
                        onClick={() => handleToggleGroup(g.id)}
                        className={`px-3 py-1.5 font-bold text-xs rounded-lg transition ${
                          g.is_active
                            ? "bg-red-50 text-red-600 hover:bg-red-100"
                            : "bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                        }`}
                      >
                        {g.is_active ? "O'chirish" : "Faollashtirish"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. O'QUVCHILAR BO'LIMI */}
        {activeTab === "students" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-base font-extrabold text-slate-800">
                O'quvchilar ro'yxati ({filteredStudents.length})
              </h2>
              <input
                type="text"
                placeholder="Qidirish (ism, tel, guruh)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3.5 py-1.5 bg-white border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 outline-none w-56"
              />
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-3.5">O'quvchi</th>
                    <th className="p-3.5">Guruh</th>
                    <th className="p-3.5">Telefon</th>
                    <th className="p-3.5">Sana</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredStudents.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/60 transition">
                      <td className="p-3.5 font-bold text-slate-900">
                        {s.full_name}
                        {s.username && (
                          <span className="block text-[10px] text-blue-600 font-normal">
                            @{s.username}
                          </span>
                        )}
                      </td>
                      <td className="p-3.5">
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-800 rounded-md font-semibold">
                          {s.group_name}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono">{s.phone || "-"}</td>
                      <td className="p-3.5 text-slate-400">{s.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 5. TO'LOVLAR BO'LIMI */}
        {activeTab === "payments" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <h2 className="text-base font-extrabold text-slate-800">
                To'lovlar boshqaruvi ({filteredPayments.length})
              </h2>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <select
                  value={paymentFilter}
                  onChange={(e) => setPaymentFilter(e.target.value)}
                  className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 outline-none"
                >
                  <option value="all">Barchasi</option>
                  <option value="pending">⏳ Kutilayotgan</option>
                  <option value="confirmed">✅ Tasdiqlangan</option>
                  <option value="rejected">❌ Rad etilgan</option>
                </select>
              </div>
            </div>

            <div className="space-y-3">
              {filteredPayments.map((p) => (
                <div
                  key={p.id}
                  className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-extrabold text-slate-900 text-sm">
                        {p.student_name}
                      </span>
                      <span
                        className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                          p.status === "confirmed"
                            ? "bg-emerald-100 text-emerald-800"
                            : p.status === "pending"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {p.status === "confirmed"
                          ? "✅ To'langan"
                          : p.status === "pending"
                          ? "⏳ Kutilmoqda"
                          : "❌ Rad etilgan"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      Guruh: <b className="text-slate-700">{p.group_name}</b> • Usul:{" "}
                      <b className="uppercase">{p.method}</b> • Sana: {p.created_at}
                    </p>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-4 w-full sm:w-auto border-t sm:border-t-0 pt-2 sm:pt-0">
                    <div className="text-right">
                      <div className="font-black text-slate-900 text-sm">
                        {p.amount.toLocaleString()} so'm
                      </div>
                      {p.discount_amount > 0 && (
                        <div className="text-[10px] text-emerald-600 font-bold">
                          Chegirma: {p.discount_amount.toLocaleString()} so'm
                        </div>
                      )}
                    </div>

                    {p.status === "pending" && (
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => handleApprovePayment(p.id)}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl transition shadow active:scale-95"
                        >
                          ✅ Tasdiqlash
                        </button>
                        <button
                          onClick={() => handleRejectPayment(p.id)}
                          className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 font-bold text-xs rounded-xl transition active:scale-95"
                        >
                          Rad etish
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 6. BROADCAST BO'LIMI */}
        {activeTab === "broadcast" && (
          <div className="max-w-xl mx-auto bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-base font-extrabold text-slate-800">
              📢 Ommaviy Xabar (Broadcast)
            </h2>
            <form onSubmit={handleSendBroadcast} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Kimlarga yuborilsin:
                </label>
                <select
                  value={broadcastRole}
                  onChange={(e) => setBroadcastRole(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 outline-none"
                >
                  <option value="all">Barcha foydalanuvchilar</option>
                  <option value="student">Faqat o'quvchilar</option>
                  <option value="teacher">Faqat o'qituvchilar</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Xabar matni (HTML formatida):
                </label>
                <textarea
                  rows={5}
                  value={broadcastText}
                  onChange={(e) => setBroadcastText(e.target.value)}
                  placeholder="Xabaringizni yozing..."
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-blue-500"
                ></textarea>
              </div>

              <button
                type="submit"
                disabled={broadcasting || !broadcastText.trim()}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow disabled:opacity-50"
              >
                {broadcasting ? "Yuborilmoqda..." : "🚀 Xabarni Yuborish"}
              </button>

              {broadcastResult && (
                <div className="bg-emerald-50 text-emerald-800 p-3 rounded-xl text-xs font-bold text-center">
                  ✅ {broadcastResult.message}
                </div>
              )}
            </form>
          </div>
        )}
      </main>

      {/* MODAL: KURS QO'SHISH / TAHRIRLASH */}
      {showCourseModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <h3 className="font-extrabold text-slate-900 text-base mb-4">
              {editingCourse ? "✏️ Kursni Tahrirlash" : "➕ Yangi Kurs Yaratish"}
            </h3>

            <form onSubmit={handleSaveCourse} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-600 mb-1">Kurs nomi (O'zbekcha):</label>
                <input
                  type="text"
                  required
                  placeholder="Masalan: General English B1"
                  value={courseForm.title_uz}
                  onChange={(e) => setCourseForm({ ...courseForm, title_uz: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Turi:</label>
                  <select
                    value={courseForm.type}
                    onChange={(e) => setCourseForm({ ...courseForm, type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  >
                    <option value="General">General English</option>
                    <option value="IELTS">IELTS</option>
                    <option value="CEFR">CEFR</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-600 mb-1">Daraja:</label>
                  <select
                    value={courseForm.level}
                    onChange={(e) => setCourseForm({ ...courseForm, level: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  >
                    {["A1", "A2", "B1", "B2", "C1", "C2"].map((lvl) => (
                      <option key={lvl} value={lvl}>
                        {lvl}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Oylik narx (so'm):</label>
                  <input
                    type="number"
                    required
                    placeholder="1500000"
                    value={courseForm.price}
                    onChange={(e) => setCourseForm({ ...courseForm, price: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-600 mb-1">1 dars narxi (ixtiyoriy):</label>
                  <input
                    type="number"
                    placeholder="Avto hisob"
                    value={courseForm.price_per_lesson}
                    onChange={(e) => setCourseForm({ ...courseForm, price_per_lesson: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Davomiyligi (oy):</label>
                  <input
                    type="number"
                    min={1}
                    value={courseForm.duration_months}
                    onChange={(e) => setCourseForm({ ...courseForm, duration_months: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-600 mb-1">Dars/hafta:</label>
                  <input
                    type="number"
                    min={1}
                    max={7}
                    value={courseForm.lessons_per_week}
                    onChange={(e) => setCourseForm({ ...courseForm, lessons_per_week: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Tavsif:</label>
                <textarea
                  rows={2}
                  placeholder="Kurs haqida qisqacha ma'lumot..."
                  value={courseForm.description_uz}
                  onChange={(e) => setCourseForm({ ...courseForm, description_uz: e.target.value })}
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                ></textarea>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCourseModal(false)}
                  className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow"
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
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <h3 className="font-extrabold text-slate-900 text-base mb-4">
              {editingGroup ? "✏️ Guruhni Tahrirlash" : "➕ Yangi Guruh Yaratish"}
            </h3>

            <form onSubmit={handleSaveGroup} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-600 mb-1">Kursni tanlang:</label>
                <select
                  value={groupForm.course_id}
                  onChange={(e) => setGroupForm({ ...groupForm, course_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title_uz || c.title?.uz} ({c.level}) - {c.price.toLocaleString()} so'm
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Guruh nomi:</label>
                <input
                  type="text"
                  required
                  placeholder="Masalan: B1 - Dush/Chor/Jum 18:30"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">O'qituvchi:</label>
                <select
                  value={groupForm.teacher_id}
                  onChange={(e) => setGroupForm({ ...groupForm, teacher_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                >
                  <option value="">Tayinlanmagan</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.full_name} (@{t.username || "username yo'q"})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Dars vaqti:</label>
                  <input
                    type="text"
                    placeholder="18:30"
                    value={groupForm.schedule_time}
                    onChange={(e) => setGroupForm({ ...groupForm, schedule_time: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-600 mb-1">Max o'quvchilar:</label>
                  <input
                    type="number"
                    min={1}
                    value={groupForm.max_students}
                    onChange={(e) => setGroupForm({ ...groupForm, max_students: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-600 mb-1">Xona / Manzil:</label>
                <input
                  type="text"
                  placeholder="3-xona / Asosiy bino"
                  value={groupForm.room}
                  onChange={(e) => setGroupForm({ ...groupForm, room: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGroupModal(false)}
                  className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow"
                >
                  Saqlash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
