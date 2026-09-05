import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { getTelegramLanguage, syncUserLanguage } from "../lib/telegram";
import LanguageSwitcher from "../components/LanguageSwitcher";
import TestBuilder from "./TestBuilder";

export default function TeacherDashboard({ onSwitchMode, embedded = false }) {
  const [lang, setLang] = useState(getTelegramLanguage);
  const [activeTab, setActiveTab] = useState("groups"); // groups, students, builder

  const handleLanguageChange = (newLang) => {
    setLang(newLang);
    syncUserLanguage(newLang);
  };
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchWorkspace = () => {
    setLoading(true);
    setError(null);
    apiClient
      .get("/api/teacher/workspace")
      .then((res) => {
        setWorkspace(res.data);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || err.message);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchWorkspace();
  }, []);

  const groups = workspace?.groups || [];
  const stats = workspace?.academic_stats || { total_groups: 0, total_students: 0, active_tests: 0 };

  // All students from teacher's groups
  const allStudents = [];
  const seenStudentIds = new Set();
  groups.forEach((g) => {
    (g.students || []).forEach((s) => {
      if (!seenStudentIds.has(s.id)) {
        seenStudentIds.add(s.id);
        allStudents.push({ ...s, group_name: g.name });
      }
    });
  });

  const filteredStudents = allStudents.filter((s) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      (s.full_name && s.full_name.toLowerCase().includes(term)) ||
      (s.phone && s.phone.includes(term)) ||
      (s.username && s.username.toLowerCase().includes(term))
    );
  });

  const contentJsx = (
    <main className={embedded ? "space-y-5" : "max-w-6xl mx-auto p-4 space-y-5 relative z-10"}>
      {error && (
        <div className="glass-panel border border-red-500/30 text-red-300 p-4 rounded-2xl text-xs flex items-center justify-between shadow-xl">
          <span>⚠️ {error}</span>
          <button onClick={fetchWorkspace} className="underline font-black">
            Qayta urinish
          </button>
        </div>
      )}

      {/* 1. ACADEMIC KPI CARDS */}
      {activeTab !== "builder" && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
            <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">🏢</span>
            <div className="text-2xl font-black text-white">{stats.total_groups}</div>
            <div className="text-[11px] text-slate-400 font-bold">Mening Guruhlarim</div>
          </div>

          <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
            <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">🎓</span>
            <div className="text-2xl font-black text-white">{stats.total_students}</div>
            <div className="text-[11px] text-slate-400 font-bold">Mening O'quvchilarim</div>
          </div>

          <div className="glass-card rounded-2xl p-4 border border-purple-500/30 shadow-xl col-span-2 sm:col-span-1 relative overflow-hidden group">
            <span className="text-2xl mb-1 block group-hover:scale-110 transition-transform">🛠</span>
            <div className="text-2xl font-black text-purple-400">{stats.active_tests}</div>
            <div className="text-[11px] text-slate-400 font-bold">Faol Placement Testlar</div>
          </div>
        </div>
      )}

      {/* 2. TAB: MENING GURUHLARIM */}
      {activeTab === "groups" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-black text-white">Mening Guruhlarim ({groups.length})</h2>
            <span className="text-xs text-slate-400">Sizga biriktirilgan darslar</span>
          </div>

          {groups.length === 0 ? (
            <div className="glass-panel rounded-3xl p-8 border border-slate-800 text-center space-y-3">
              <span className="text-4xl block">📚</span>
              <h3 className="font-bold text-white text-sm">Sizga hali guruh biriktirilmagan</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Administrator yangi guruh ochib sizni ustoz etib belgilashi bilan guruhlaringiz shu yerda paydo bo'ladi.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {groups.map((g) => (
                <div
                  key={g.id}
                  className="glass-card rounded-3xl p-5 border border-slate-800/80 hover:border-purple-500/40 transition shadow-xl space-y-4 relative overflow-hidden"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-black text-white text-base">{g.name}</h3>
                        <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-black">
                          {g.level}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-semibold mt-0.5">{g.course_name}</p>
                    </div>

                    <span className="px-2.5 py-1 rounded-full text-xs font-black bg-slate-900 border border-slate-700 text-slate-300">
                      👥 {g.enrolled_count} / {g.max_students}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 bg-slate-950/60 p-3 rounded-2xl border border-slate-800/60">
                    <div>
                      <span className="text-[10px] text-slate-500 block font-bold">Xona:</span>
                      <span className="font-bold text-white">📍 {g.room || "Asosiy xona"}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block font-bold">Dars vaqti:</span>
                      <span className="font-bold text-white">
                        ⏰ {Array.isArray(g.schedule) && g.schedule.length > 0 && typeof g.schedule[0] === "object" ? g.schedule[0].time : "18:00"}
                      </span>
                    </div>
                  </div>

                  {/* Quick classroom buttons */}
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    {g.group_chat_link ? (
                      <a
                        href={g.group_chat_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="py-2.5 px-3 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-black transition flex items-center justify-center gap-1.5 active:scale-95"
                      >
                        <span>💬</span>
                        <span>Guruh Chati</span>
                      </a>
                    ) : (
                      <button
                        disabled
                        className="py-2.5 px-3 bg-slate-800/40 text-slate-500 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5"
                      >
                        <span>💬</span>
                        <span>Chat yo'q</span>
                      </button>
                    )}

                    <button
                      onClick={() => setSelectedGroup(selectedGroup?.id === g.id ? null : g)}
                      className="py-2.5 px-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-black transition flex items-center justify-center gap-1.5 active:scale-95 shadow-md shadow-purple-600/25"
                    >
                      <span>👥</span>
                      <span>{selectedGroup?.id === g.id ? "Yopish" : "O'quvchilar"}</span>
                    </button>
                  </div>

                  {/* Group Student Roster Accordion */}
                  {selectedGroup?.id === g.id && (
                    <div className="pt-3 border-t border-slate-800/80 space-y-2">
                      <h4 className="text-xs font-black text-slate-300">
                        Guruh O'quvchilari ({g.students?.length || 0}):
                      </h4>
                      {!g.students || g.students.length === 0 ? (
                        <p className="text-xs text-slate-500 italic">Hozircha o'quvchilar a'zo bo'lmagan.</p>
                      ) : (
                        <div className="space-y-1.5 max-h-48 overflow-y-auto no-scrollbar pr-1">
                          {g.students.map((st, idx) => (
                            <div
                              key={st.id}
                              className="flex items-center justify-between p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-xs"
                            >
                              <div className="flex items-center gap-2">
                                <span className="w-5 h-5 rounded-full bg-purple-600/20 text-purple-300 text-[10px] font-black flex items-center justify-center">
                                  {idx + 1}
                                </span>
                                <div>
                                  <div className="font-bold text-white">{st.full_name}</div>
                                  <div className="text-[10px] text-slate-400">
                                    {st.username ? `@${st.username}` : "username yo'q"}
                                  </div>
                                </div>
                              </div>
                              <span className="text-slate-300 text-[11px] font-semibold">{st.phone}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 3. TAB: MENING O'QUVCHILARIM */}
      {activeTab === "students" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <h2 className="text-base font-black text-white">Barcha O'quvchilarim ({allStudents.length})</h2>

            <input
              type="text"
              placeholder="O'quvchini qidirish..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500 font-semibold"
            />
          </div>

          <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 font-extrabold uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="p-3.5">O'quvchi</th>
                    <th className="p-3.5">Guruh</th>
                    <th className="p-3.5">Telefon</th>
                    <th className="p-3.5">A'zo bo'lgan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredStudents.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="p-8 text-center text-slate-500 font-medium">
                        O'quvchilar topilmadi.
                      </td>
                    </tr>
                  ) : (
                    filteredStudents.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3.5 font-bold text-white flex items-center gap-2">
                          <span className="w-7 h-7 rounded-lg bg-purple-600/20 text-purple-300 font-black flex items-center justify-center text-[10px]">
                            {s.full_name?.charAt(0) || "U"}
                          </span>
                          <div>
                            <div>{s.full_name}</div>
                            <div className="text-[10px] text-slate-400 font-normal">
                              {s.username ? `@${s.username}` : "username yo'q"}
                            </div>
                          </div>
                        </td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold">
                            {s.group_name}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-300 font-semibold">{s.phone}</td>
                        <td className="p-3.5 text-slate-400 text-[11px]">{s.enrolled_at || "—"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 4. TAB: TEST BUILDER & AI */}
      {activeTab === "builder" && (
        <div className="space-y-4">
          <div className="glass-panel rounded-3xl p-4 border border-purple-500/30 flex items-center justify-between shadow-xl">
            <div>
              <h3 className="font-black text-white text-sm">🛠 AI & Qo'lda Test Yaratish</h3>
              <p className="text-xs text-slate-400">
                PDF testlarni yuklang yoki yangi CEFR/IELTS savollarini bir zumda shakllantiring.
              </p>
            </div>
          </div>

          <TestBuilder onSwitchMode={onSwitchMode} />
        </div>
      )}
    </main>
  );

  const subNavJsx = (
    <div className="flex gap-1.5 overflow-x-auto no-scrollbar border-t border-slate-800/80 pt-2 pb-2 text-xs font-bold">
      <button
        onClick={() => setActiveTab("groups")}
        className={`py-2 px-3.5 rounded-xl flex items-center gap-2 transition-all ${
          activeTab === "groups"
            ? "bg-purple-600 text-white shadow-lg shadow-purple-600/25 font-black"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
        }`}
      >
        <span>🏢</span>
        <span>Mening Guruhlarim</span>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
          {groups.length}
        </span>
      </button>

      <button
        onClick={() => setActiveTab("students")}
        className={`py-2 px-3.5 rounded-xl flex items-center gap-2 transition-all ${
          activeTab === "students"
            ? "bg-purple-600 text-white shadow-lg shadow-purple-600/25 font-black"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
        }`}
      >
        <span>👥</span>
        <span>Mening O'quvchilarim</span>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
          {allStudents.length}
        </span>
      </button>

      <button
        onClick={() => setActiveTab("builder")}
        className={`py-2 px-3.5 rounded-xl flex items-center gap-2 transition-all ${
          activeTab === "builder"
            ? "bg-purple-600 text-white shadow-lg shadow-purple-600/25 font-black"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
        }`}
      >
        <span>🛠</span>
        <span>Test Builder & AI</span>
      </button>
    </div>
  );

  if (embedded) {
    return (
      <div className="space-y-4">
        {subNavJsx}
        {contentJsx}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 pb-20 relative overflow-hidden font-sans">
      {/* Ambient glowing background orbs */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/3 left-10 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header */}
      <header className="bg-[#0a0f1d]/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30 shadow-xl">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center text-xl shadow-lg shadow-purple-500/20">
              👨‍🏫
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-black text-white text-base leading-tight">
                  Ustoz Kabineti
                </h1>
                <span className="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-black uppercase tracking-wider">
                  Teacher View
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-semibold">
                {workspace?.teacher_name ? `Assalomu alaykum, ${workspace.teacher_name}` : "Darslar va O'quvchilar Boshqaruvi"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <LanguageSwitcher currentLang={lang} onChangeLang={handleLanguageChange} />

            {onSwitchMode && (
              <button
                onClick={() => onSwitchMode("admin")}
                className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1.5"
                title="Admin boshqaruviga o'tish"
              >
                <span>👑</span>
                <span>Admin Dashboard</span>
              </button>
            )}

            <button
              onClick={fetchWorkspace}
              className="p-2 text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 rounded-xl transition border border-slate-700/60"
              title="Yangilash"
            >
              🔄
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-6xl mx-auto px-4">
          {subNavJsx}
        </div>
      </header>

      {contentJsx}
    </div>
  );
}
