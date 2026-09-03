import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { getTelegramLanguage } from "../lib/telegram";

export default function StudentProgress({ onSwitchMode }) {
  const [lang] = useState(getTelegramLanguage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get("/api/student/progress")
      .then((res) => setProgress(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, []);

  const badgeIcons = {
    starter: { icon: "🌱", title: "Starter", desc: "Birinchi testni topshirdi", glow: "from-emerald-500/20 to-teal-500/10", border: "border-emerald-500/40" },
    regular: { icon: "⚡️", title: "Regular", desc: "10 ta darsda to'liq qatnashdi", glow: "from-amber-500/20 to-yellow-500/10", border: "border-amber-500/40" },
    master: { icon: "🏆", title: "Master", desc: "Testlarda 90%+ ball to'pladi", glow: "from-purple-500/20 to-pink-500/10", border: "border-purple-500/40" },
    homework_hero: { icon: "📚", title: "Homework Hero", desc: "Barcha uy vazifalarini topshirdi", glow: "from-blue-500/20 to-cyan-500/10", border: "border-blue-500/40" },
    ambassador: { icon: "👥", title: "Ambassador", desc: "Do'stini kursga taklif qildi", glow: "from-rose-500/20 to-orange-500/10", border: "border-rose-500/40" },
  };

  const attPercent = progress?.attendance_percent ?? 100;
  const avgScore = progress?.average_test_score ?? 0;
  const userBadges = progress?.badges || ["starter"];

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 pb-16 relative overflow-hidden">
      {/* Ambient glowing orbs */}
      <div className="absolute top-0 right-1/4 w-80 h-80 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-20 left-10 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Header */}
      <header className="bg-[#0a0f1d]/85 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30 px-4 py-3.5 flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-black shadow-lg shadow-indigo-500/30 text-sm">
            📊
          </div>
          <div>
            <h1 className="font-black text-sm text-white leading-tight">O'quvchi Natijalari</h1>
            <p className="text-[10px] text-slate-400 font-semibold">Statistika & Gamifikatsiya</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onSwitchMode("test")}
            className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1.5"
          >
            <span>🎯</span>
            <span>Testlar</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-md mx-auto p-4 space-y-4 relative z-10">
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center text-center">
            <div className="relative w-14 h-14 mb-4">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping"></div>
              <div className="w-14 h-14 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
            </div>
            <p className="text-slate-400 text-xs font-semibold">Statistika tahlil qilinmoqda...</p>
          </div>
        ) : error ? (
          <div className="glass-panel border border-red-500/30 text-red-300 p-4 rounded-2xl text-xs font-medium text-center shadow-xl">
            ⚠️ {error}
          </div>
        ) : (
          <>
            {/* Gamified Hero Card */}
            <div className="relative rounded-3xl p-5 bg-gradient-to-br from-indigo-900/80 via-slate-900/90 to-purple-950/80 border border-indigo-500/30 shadow-2xl overflow-hidden">
              <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-indigo-500/20 rounded-full blur-2xl pointer-events-none"></div>
              
              <div className="flex items-center justify-between mb-4">
                <div>
                  <span className="inline-flex items-center gap-1 text-[10px] font-black px-2.5 py-0.5 bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 rounded-full uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                    Faol O'quvchi
                  </span>
                  <h2 className="text-lg font-black text-white mt-1">O'zlashtirish Darajasi</h2>
                </div>
                <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center text-2xl border border-white/10 shadow-inner">
                  🚀
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-extrabold">
                  <span className="text-slate-300">Davomat Intizomi</span>
                  <span className="text-emerald-400">{attPercent}%</span>
                </div>
                <div className="w-full bg-slate-800/90 h-3 rounded-full overflow-hidden p-0.5 border border-slate-700">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 rounded-full transition-all duration-1000 shadow-sm"
                    style={{ width: `${Math.min(attPercent, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* KPI Metric Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-2xl">📈</span>
                  <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    TESTLAR
                  </span>
                </div>
                <div className="text-2xl font-black text-white">{avgScore}%</div>
                <div className="text-[11px] text-slate-400 font-bold">O'rtacha Test Bali</div>
                <div className="text-[10px] text-indigo-400 font-semibold mt-1">
                  {progress?.tests_taken ?? 0} ta test topshirilgan
                </div>
              </div>

              <div className="glass-card rounded-2xl p-4 border border-slate-800 shadow-xl relative overflow-hidden group">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-2xl">📅</span>
                  <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    DAVOMAT
                  </span>
                </div>
                <div className="text-2xl font-black text-emerald-400">{attPercent}%</div>
                <div className="text-[11px] text-slate-400 font-bold">Qatnashish Ko'rsatkichi</div>
                <div className="text-[10px] text-slate-400 font-semibold mt-1">
                  {progress?.total_lessons_tracked ?? 0} ta dars qayd etilgan
                </div>
              </div>
            </div>

            {/* Badges & Gamification Showcase */}
            <div className="glass-panel rounded-3xl p-5 border border-slate-800 shadow-2xl space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-black text-xs uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <span>🏅</span>
                  <span>Unvonlar va Yutuqlar</span>
                </h3>
                <span className="text-[10px] font-extrabold px-2.5 py-0.5 bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 rounded-full">
                  {userBadges.length} ta yutuq
                </span>
              </div>

              <div className="grid grid-cols-1 gap-2.5">
                {Object.entries(badgeIcons).map(([key, info]) => {
                  const hasBadge = userBadges.includes(key);
                  return (
                    <div
                      key={key}
                      className={`flex items-center gap-3.5 p-3.5 rounded-2xl border transition-all ${
                        hasBadge
                          ? `bg-gradient-to-r ${info.glow} ${info.border} shadow-lg shadow-indigo-500/5 text-white`
                          : "bg-slate-900/40 border-slate-800/80 opacity-40 text-slate-500 grayscale"
                      }`}
                    >
                      <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-white/10 flex items-center justify-center text-xl shrink-0">
                        {info.icon}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-0.5">
                          <h4 className="font-black text-xs text-white">{info.title}</h4>
                          {hasBadge ? (
                            <span className="text-[9px] font-black px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 rounded-md">
                              ✓ QO'LGA KIRITILDI
                            </span>
                          ) : (
                            <span className="text-[9px] font-bold text-slate-600">Qulflangan</span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 leading-tight">{info.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Motivation Box */}
            <div className="glass-card rounded-2xl p-4 border border-indigo-500/30 shadow-xl flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xl shrink-0">
                💡
              </div>
              <div>
                <h4 className="text-xs font-black text-white mb-0.5">Doimiy Davomat — Muvaffaqiyat Kaliti!</h4>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Darslarni qoldirmang, muntazam test topshiring va rasmiy sertifikatga ega bo'ling.
                </p>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
