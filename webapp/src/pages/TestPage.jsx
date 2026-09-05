import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { getTelegramLanguage, setTelegramLanguage, syncUserLanguage } from "../lib/telegram";
import { getTranslation } from "../lib/translations";

const TEST_TYPES_BASE = [
  {
    id: "General",
    badge: "General English",
    icon: "🌱",
    color: "from-emerald-500/20 via-teal-500/10 to-transparent",
    border: "border-emerald-500/30 hover:border-emerald-400",
    activeBorder: "border-emerald-500 bg-emerald-500/15 shadow-lg shadow-emerald-500/20",
    tagColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  },
  {
    id: "CEFR",
    badge: "CEFR Track",
    icon: "🎯",
    color: "from-blue-500/20 via-indigo-500/10 to-transparent",
    border: "border-blue-500/30 hover:border-blue-400",
    activeBorder: "border-blue-500 bg-blue-500/15 shadow-lg shadow-blue-500/20",
    tagColor: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  },
  {
    id: "IELTS",
    badge: "IELTS Prep",
    icon: "🇬🇧",
    color: "from-purple-500/20 via-pink-500/10 to-transparent",
    border: "border-purple-500/30 hover:border-purple-400",
    activeBorder: "border-purple-500 bg-purple-500/15 shadow-lg shadow-purple-500/20",
    tagColor: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  },
];

const LEVELS = [
  { code: "A1", name: "Beginner", ielts: "Band 3.0-3.5", color: "from-emerald-500 to-teal-400" },
  { code: "A2", name: "Elementary", ielts: "Band 4.0-4.5", color: "from-teal-500 to-cyan-400" },
  { code: "B1", name: "Intermediate", ielts: "Band 5.0-5.5", color: "from-cyan-500 to-blue-400" },
  { code: "B2", name: "Upper-Int.", ielts: "Band 6.0-6.5", color: "from-blue-500 to-indigo-400" },
  { code: "C1", name: "Advanced", ielts: "Band 7.0-8.0", color: "from-indigo-500 to-purple-400" },
  { code: "C2", name: "Proficiency", ielts: "Band 8.5-9.0", color: "from-purple-500 to-pink-400" },
];

function LanguageSwitcher({ currentLang, onChangeLang }) {
  const languages = [
    { code: "uz", label: "UZ" },
    { code: "ru", label: "RU" },
    { code: "en", label: "EN" },
  ];

  return (
    <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 shadow-inner text-xs font-bold">
      {languages.map((l) => (
        <button
          key={l.code}
          onClick={() => onChangeLang(l.code)}
          className={`px-2.5 py-1 rounded-lg transition-all text-[11px] font-bold ${
            currentLang === l.code
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/30 font-extrabold"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

function CategoryAndLevelSelect({
  lang,
  onChangeLang,
  selectedType,
  onSelectType,
  onSelectLevel,
  onSwitchMode,
}) {
  const t = getTranslation(lang);

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 flex flex-col items-center p-4 max-w-lg mx-auto relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-0 left-1/4 w-72 h-72 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Navbar */}
      <div className="w-full flex justify-between items-center mt-2 mb-6 z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-black text-white text-xs shadow-lg shadow-indigo-500/30">
            A
          </div>
          <div>
            <span className="text-xs font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
              ALPHA CENTER
            </span>
            <span className="block text-[9px] text-slate-400 font-semibold uppercase tracking-wider">
              Smart Testing Portal
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {onSwitchMode && (
            <button
              onClick={() => onSwitchMode("progress")}
              className="px-2.5 py-1 bg-slate-800/80 hover:bg-slate-700/80 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-bold transition active:scale-95 flex items-center gap-1"
            >
              <span>📊</span>
              <span>Progress</span>
            </button>
          )}
          <LanguageSwitcher currentLang={lang} onChangeLang={onChangeLang} />
        </div>
      </div>

      {/* Hero Header */}
      <div className="w-full text-center mb-6 z-10">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-bold mb-2.5">
          <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-pulse"></span>
          AI Diagnostic Placement
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-snug">
          {t.appTitle}
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-sm mx-auto">
          {t.appSubtitle}
        </p>
      </div>

      {/* STEP 1: Track Selection */}
      <div className="w-full mb-6 z-10">
        <div className="flex items-center justify-between mb-2.5">
          <label className="text-xs font-extrabold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] flex items-center justify-center font-black">1</span>
            {t.step1Title}
          </label>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {TEST_TYPES_BASE.map((item) => {
            const isSelected = selectedType === item.id;
            const typeInfo = t.types[item.id] || {};
            return (
              <button
                key={item.id}
                onClick={() => onSelectType(item.id)}
                className={`relative p-3.5 rounded-2xl text-left transition-all border ${
                  isSelected
                    ? item.activeBorder
                    : `bg-slate-900/60 ${item.border} hover:bg-slate-800/60`
                } active:scale-[0.98] group`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl group-hover:scale-110 transition-transform">
                    {item.icon}
                  </span>
                  <span className={`text-[10px] font-black px-2 py-0.5 rounded-md border ${item.tagColor}`}>
                    {item.badge}
                  </span>
                </div>
                <div className="font-extrabold text-sm text-white mb-0.5">
                  {typeInfo.title || item.id}
                </div>
                <div className="text-[11px] text-slate-400 line-clamp-1">
                  {typeInfo.subtitle || ""}
                </div>
                
                {isSelected && (
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-indigo-500 rounded-full border-2 border-[#0a0f1d]"></div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* STEP 2: Level Selection */}
      <div className="w-full z-10 pb-8">
        <div className="flex items-center justify-between mb-2.5">
          <label className="text-xs font-extrabold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] flex items-center justify-center font-black">2</span>
            {t.step2Title.replace("{selectedType}", selectedType)}
          </label>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
          {LEVELS.map((lvl) => {
            const lvlDesc = t.levels[lvl.code]?.desc || "";
            return (
              <button
                key={lvl.code}
                onClick={() => onSelectLevel(lvl.code)}
                className="relative bg-slate-900/70 hover:bg-slate-800/90 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-3.5 text-left transition-all shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 active:scale-95 group overflow-hidden"
              >
                {/* Decorative accent */}
                <div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl ${lvl.color} opacity-10 group-hover:opacity-25 rounded-bl-full transition-opacity`}></div>

                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-xl font-black bg-clip-text text-transparent bg-gradient-to-r ${lvl.color}`}>
                    {lvl.code}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 border border-slate-700/60">
                    {selectedType === "IELTS" ? lvl.ielts : lvl.name}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 group-hover:text-slate-300 transition">
                  {lvlDesc}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function getInitialParams() {
  const params = new URLSearchParams(window.location.search);
  const initialType = params.get("type") || "General";
  const initialLevel = params.get("level");
  const isTrial = params.get("is_trial") === "true" || params.get("flow") === "trial";
  return {
    type: ["IELTS", "CEFR", "GENERAL"].includes(initialType.toUpperCase())
      ? initialType === "General" ? "General" : initialType.toUpperCase()
      : "General",
    level:
      initialLevel && LEVELS.some((l) => l.code === initialLevel.toUpperCase())
        ? initialLevel.toUpperCase()
        : null,
    isTrial: isTrial,
  };
}

export default function TestPage({ onSwitchMode }) {
  const [lang, setLang] = useState(getTelegramLanguage);
  const [initialParams] = useState(getInitialParams);
  const [selectedType, setSelectedType] = useState(initialParams.type);
  const [level, setLevel] = useState(initialParams.level);
  const [test, setTest] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [reviewFilter, setReviewFilter] = useState("all"); // all, correct, incorrect

  const t = getTranslation(lang);

  const handleLanguageChange = (newLang) => {
    setLang(newLang);
    syncUserLanguage(newLang);
  };

  useEffect(() => {
    if (!level) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setAnswers({});

    apiClient
      .get(`/api/tests/by-level/${level}?type=${selectedType}`)
      .then((res) => setTest(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [level, selectedType]);

  const selectAnswer = (questionId, option) => {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const submit = () => {
    if (submitting || !test) return;
    setSubmitting(true);
    setError(null);

    const payload = {
      answers: Object.entries(answers).map(([question_id, answer]) => ({
        question_id,
        answer,
      })),
      is_trial: initialParams.isTrial || false,
    };

    apiClient
      .post(`/api/tests/${test.id}/submit`, payload)
      .then((res) => setResult(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setSubmitting(false));
  };

  // 1. Agar daraja tanlanmagan bo'lsa
  if (!level) {
    return (
      <CategoryAndLevelSelect
        lang={lang}
        onChangeLang={handleLanguageChange}
        selectedType={selectedType}
        onSelectType={setSelectedType}
        onSelectLevel={setLevel}
        onSwitchMode={onSwitchMode}
      />
    );
  }

  // 2. Yuklanish holati
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0f1d] flex flex-col items-center justify-center p-4 text-center">
        <div className="relative w-16 h-16 mb-4">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping"></div>
          <div className="w-16 h-16 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
        </div>
        <h3 className="text-white font-extrabold text-base mb-1">{t.loading}</h3>
        <p className="text-slate-400 text-xs">{selectedType} — {level} darajasi tayyorlanmoqda...</p>
      </div>
    );
  }

  // 3. 24 soatlik Cooldown holati
  if (test?.cooldown?.active && !result) {
    return (
      <div className="min-h-screen bg-[#0a0f1d] flex flex-col items-center justify-center p-4 text-center">
        <div className="glass-panel rounded-3xl p-6 max-w-sm w-full border border-amber-500/30 shadow-2xl relative">
          <div className="w-16 h-16 bg-amber-500/15 border border-amber-500/30 text-amber-400 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4 glow-amber">
            ⏳
          </div>
          <h2 className="text-lg font-black text-white mb-2">Qayta Topshirish Cheklovi</h2>
          <p className="text-slate-300 text-xs leading-relaxed mb-5">
            Siz ushbu <b className="text-amber-300">{level}</b> darajali testni yaqinda topshirgansiz. Qayta topshirish uchun yana <b className="text-amber-300">{test.cooldown.remaining_hours} soat</b> kuting yoki hoziroq 1 daraja pastroq darajani topshiring.
          </p>
          <div className="flex flex-col gap-2.5">
            <button
              onClick={() => {
                setLevel(test.cooldown.lower_level);
                setAnswers({});
              }}
              className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-black shadow-lg shadow-indigo-500/25 active:scale-95 transition-all"
            >
              🎯 {test.cooldown.lower_level} Testini Boshlash
            </button>
            <button
              onClick={() => {
                setLevel(null);
                setTest(null);
              }}
              className="w-full py-3 bg-slate-800 text-slate-300 rounded-xl text-xs font-bold hover:bg-slate-700 active:scale-95 transition-all border border-slate-700"
            >
              ⬅️ Boshqa daraja tanlash
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 4. Xatolik holati
  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0f1d] flex flex-col items-center justify-center p-4 text-center">
        <div className="glass-panel rounded-3xl border border-red-500/30 p-6 max-w-sm w-full shadow-2xl">
          <div className="w-14 h-14 rounded-2xl bg-red-500/15 border border-red-500/30 text-red-400 flex items-center justify-center text-2xl mx-auto mb-3">
            ⚠️
          </div>
          <h2 className="text-lg font-bold text-white mb-1">{t.errorTitle}</h2>
          <p className="text-slate-400 text-xs mb-5">{error}</p>
          <button
            onClick={() => {
              setLevel(null);
              setError(null);
            }}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl py-3 font-bold text-xs transition active:scale-95 shadow-lg shadow-indigo-600/30"
          >
            {t.changeTest}
          </button>
        </div>
      </div>
    );
  }

  if (!test) return null;

  // 5. Natijalar va Xatolar ustida ishlash ekrani
  if (result) {
    const isPassed = result.passed;
    const reviewItems = result.review || [];
    const filteredReview = reviewItems.filter((item) => {
      if (reviewFilter === "correct") return item.is_correct;
      if (reviewFilter === "incorrect") return !item.is_correct;
      return true;
    });

    const incorrectCount = (result.total || 0) - (result.score || 0);

    return (
      <div className="min-h-screen bg-[#0a0f1d] text-slate-100 p-4 pb-20 max-w-lg mx-auto relative overflow-hidden">
        {/* Glowing ambient orbs */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-80 h-80 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>

        {/* Natija xulosasi kartasi */}
        <div className="glass-panel rounded-3xl border border-white/10 p-6 text-center space-y-4 shadow-2xl relative z-10 mb-6">
          <div className="text-5xl mb-1">{isPassed ? "🎉" : "📚"}</div>

          <div>
            <h2 className="text-xl font-black text-white">
              {isPassed ? t.resultPassedTitle : t.resultFailedTitle}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {selectedType} — {level} darajasi natijasi
            </p>
          </div>

          {/* Glowing score badge */}
          <div className="bg-slate-900/80 rounded-2xl p-5 border border-slate-800 shadow-inner">
            <div className={`text-4xl font-black mb-1 ${isPassed ? "text-emerald-400" : "text-indigo-400"}`}>
              {result.percent}%
            </div>
            <p className="text-slate-400 text-xs font-semibold">
              {t.correctAnswers
                .replace("{score}", result.score)
                .replace("{total}", result.total)}
            </p>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {isPassed ? t.resultPassedDesc : t.resultFailedDesc}
          </p>

          <div className="flex gap-2 pt-2">
            <button
              onClick={() => {
                setResult(null);
                setAnswers({});
                setLevel(null);
                setReviewFilter("all");
              }}
              className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl py-3 font-black text-xs transition shadow-lg shadow-indigo-500/25 active:scale-95"
            >
              {t.retakeTest}
            </button>
            <button
              onClick={() => {
                setLevel(null);
                setResult(null);
                setAnswers({});
                setReviewFilter("all");
              }}
              className="px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl py-3 font-bold text-xs transition active:scale-95"
            >
              ⬅️ Darajalar
            </button>
          </div>
        </div>

        {/* 🔍 SAVOLLAR TAHLILI (XATOLAR USTIDA ISHLASH) */}
        {reviewItems.length > 0 && (
          <div className="space-y-4 relative z-10">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-white flex items-center gap-1.5">
                <span>🔍</span>
                <span>Savollar Tahlili</span>
              </h3>
              <span className="text-[10px] text-slate-400 font-bold">
                {result.score}/{result.total} to'g'ri
              </span>
            </div>

            {/* Filter tab buttons */}
            <div className="flex gap-1.5 p-1 bg-slate-900/90 rounded-2xl border border-slate-800 text-xs font-bold">
              <button
                onClick={() => setReviewFilter("all")}
                className={`flex-1 py-2 rounded-xl transition text-[11px] font-bold ${
                  reviewFilter === "all"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Barchasi ({result.total})
              </button>
              <button
                onClick={() => setReviewFilter("correct")}
                className={`flex-1 py-2 rounded-xl transition text-[11px] font-bold flex items-center justify-center gap-1 ${
                  reviewFilter === "correct"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                    : "text-emerald-400 hover:bg-emerald-500/10"
                }`}
              >
                <span>✅</span>
                <span>To'g'ri ({result.score})</span>
              </button>
              <button
                onClick={() => setReviewFilter("incorrect")}
                className={`flex-1 py-2 rounded-xl transition text-[11px] font-bold flex items-center justify-center gap-1 ${
                  reviewFilter === "incorrect"
                    ? "bg-red-600 text-white shadow-md shadow-red-600/30"
                    : "text-red-400 hover:bg-red-500/10"
                }`}
              >
                <span>❌</span>
                <span>Xatolar ({incorrectCount})</span>
              </button>
            </div>

            {/* Savollar ro'yxati */}
            <div className="space-y-3">
              {filteredReview.map((item) => {
                const isCorrect = item.is_correct;
                return (
                  <div
                    key={item.id}
                    className={`glass-card rounded-2xl p-4 border transition-all ${
                      isCorrect
                        ? "border-emerald-500/30 bg-emerald-950/10"
                        : "border-red-500/30 bg-red-950/10"
                    }`}
                  >
                    {/* Header: Savol raqami & Holati */}
                    <div className="flex items-start justify-between gap-2 mb-2.5">
                      <div className="flex items-start gap-2">
                        <span
                          className={`w-6 h-6 rounded-lg font-black text-xs flex items-center justify-center shrink-0 mt-0.5 ${
                            isCorrect
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-red-500/20 text-red-300 border border-red-500/30"
                          }`}
                        >
                          {item.index}
                        </span>
                        <p className="font-bold text-slate-100 text-xs leading-snug">
                          {item.text}
                        </p>
                      </div>

                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-black shrink-0 ${
                          isCorrect
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : "bg-red-500/20 text-red-300 border border-red-500/40"
                        }`}
                      >
                        {isCorrect ? "✅ To'g'ri" : "❌ Xato"}
                      </span>
                    </div>

                    {/* Variantlar tahlili */}
                    {item.options && item.options.length > 0 ? (
                      <div className="space-y-1.5 mt-3">
                        {item.options.map((opt, optIdx) => {
                          const letter = String.fromCharCode(65 + optIdx);
                          const isUserAnswer = item.user_answer === opt;
                          const isCorrectAnswer = item.correct_answer === opt;

                          let optStyle = "bg-slate-900/50 border-slate-800 text-slate-400";
                          let badge = null;

                          if (isCorrectAnswer) {
                            optStyle = "bg-emerald-500/15 border-emerald-500/50 text-emerald-200 font-bold";
                            badge = (
                              <span className="ml-auto text-[10px] font-black text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-md border border-emerald-500/30">
                                ✓ To'g'ri javob
                              </span>
                            );
                          } else if (isUserAnswer && !isCorrect) {
                            optStyle = "bg-red-500/15 border-red-500/50 text-red-200 font-bold";
                            badge = (
                              <span className="ml-auto text-[10px] font-black text-red-400 bg-red-500/20 px-2 py-0.5 rounded-md border border-red-500/30">
                                ✗ Sizning javobingiz
                              </span>
                            );
                          }

                          return (
                            <div
                              key={opt}
                              className={`px-3 py-2 rounded-xl text-xs flex items-center gap-2 border transition ${optStyle}`}
                            >
                              <span className="w-4 h-4 rounded text-[10px] font-black flex items-center justify-center bg-slate-800 text-slate-300">
                                {letter}
                              </span>
                              <span className="flex-1">{opt}</span>
                              {badge}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      /* Ochiq va Bo'sh joy to'ldirish savollari tahlili */
                      <div className="space-y-2 mt-3 text-xs">
                        <div className={`p-3 rounded-xl border flex items-center justify-between ${
                          isCorrect ? "bg-emerald-500/15 border-emerald-500/50 text-emerald-200" : "bg-red-500/15 border-red-500/50 text-red-200"
                        }`}>
                          <div>
                            <span className="text-[10px] text-slate-400 block font-bold uppercase">Sizning javobingiz:</span>
                            <span className="font-extrabold">{item.user_answer || "(Javob yozilmagan)"}</span>
                          </div>
                          <span className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                            isCorrect ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"
                          }`}>
                            {isCorrect ? "✓ To'g'ri" : "✗ Xato"}
                          </span>
                        </div>

                        {!isCorrect && (
                          <div className="p-3 rounded-xl border bg-emerald-500/10 border-emerald-500/40 text-emerald-300">
                            <span className="text-[10px] text-emerald-400 block font-bold uppercase">To'g'ri javob:</span>
                            <span className="font-extrabold">{item.correct_answer}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 6. Test savollarini ishlash ekrani
  const answeredCount = Object.keys(answers).filter((k) => answers[k] && answers[k].trim !== undefined ? answers[k].trim().length > 0 : !!answers[k]).length;
  const totalQuestions = test.questions?.length || 0;
  const progressPercent = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

  const testTitle =
    typeof test.title === "object"
      ? test.title[lang] || test.title.uz || test.title.en || "Test"
      : test.title;

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 p-4 pb-44 max-w-lg mx-auto relative">
      {/* Sticky Top Progress Header */}
      <div className="sticky top-0 bg-[#0a0f1d]/90 backdrop-blur-md py-3 z-30 border-b border-slate-800/80 mb-5">
        <div className="flex items-center justify-between mb-2">
          <div>
            <button
              onClick={() => setLevel(null)}
              className="text-xs text-indigo-400 font-bold hover:underline mb-0.5 inline-block"
            >
              {t.back}
            </button>
            <h1 className="text-sm font-black text-white leading-tight">
              {testTitle}
            </h1>
          </div>
          
          <div className="flex items-center gap-1.5">
            <span className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-black px-2.5 py-1 rounded-lg">
              {level}
            </span>
            <LanguageSwitcher currentLang={lang} onChangeLang={handleLanguageChange} />
          </div>
        </div>

        {/* Dynamic Glowing Progress Bar */}
        <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-300 shadow-sm"
            style={{ width: `${progressPercent}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-[10px] font-bold text-slate-400 mt-1">
          <span>Jarayon: {answeredCount}/{totalQuestions} ta savol</span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
      </div>

      {/* Questions list */}
      <div className="space-y-4">
        {test.questions.map((q, idx) => {
          const isAnswered = !!answers[q.id] && (typeof answers[q.id] === "string" ? answers[q.id].trim().length > 0 : true);
          const qType = q.type || (q.options && q.options.length > 0 ? "mcq" : "short_answer");

          return (
            <div
              key={q.id}
              className={`glass-card rounded-2xl p-4 transition-all border ${
                isAnswered ? "border-indigo-500/40 bg-slate-900/80" : "border-slate-800 bg-slate-900/50"
              }`}
            >
              <div className="flex items-start gap-2.5 mb-3">
                <span className="w-6 h-6 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 font-black text-xs flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <div className="flex-1">
                  <p className="font-bold text-slate-100 text-sm leading-snug">
                    {q.text}
                  </p>
                </div>
              </div>

              {/* 1. Multiple Choice (MCQ) */}
              {qType === "mcq" && q.options && q.options.length > 0 && (
                <div className="space-y-2">
                  {q.options.map((opt, optIdx) => {
                    const isSelected = answers[q.id] === opt;
                    const letter = String.fromCharCode(65 + optIdx);
                    const cleanOpt = opt.replace(/^[A-Ea-e][\)\.\:\-\s]+/, "");
                    return (
                      <button
                        key={opt}
                        onClick={() => selectAnswer(q.id, opt)}
                        className={`w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold transition-all border flex items-center gap-2.5 ${
                          isSelected
                            ? "bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-600/25 font-bold"
                            : "bg-slate-800/60 text-slate-300 border-slate-700/60 hover:bg-slate-800 hover:border-slate-600"
                        } active:scale-[0.99]`}
                      >
                        <span className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-black ${
                          isSelected ? "bg-white text-indigo-700" : "bg-slate-700 text-slate-300"
                        }`}>
                          {letter}
                        </span>
                        <span className="flex-1">{cleanOpt}</span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* 2. True / False */}
              {qType === "true_false" && (
                <div className="grid grid-cols-2 gap-2.5 pt-1">
                  {["True", "False"].map((tfOpt) => {
                    const isSelected = (answers[q.id] || "").toLowerCase() === tfOpt.toLowerCase();
                    return (
                      <button
                        key={tfOpt}
                        type="button"
                        onClick={() => selectAnswer(q.id, tfOpt)}
                        className={`py-3 px-4 rounded-xl text-xs font-black transition-all border flex items-center justify-center gap-2 ${
                          isSelected
                            ? tfOpt === "True"
                              ? "bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-600/25"
                              : "bg-red-600 text-white border-red-500 shadow-lg shadow-red-600/25"
                            : "bg-slate-800/60 text-slate-300 border-slate-700/60 hover:bg-slate-800"
                        } active:scale-[0.98]`}
                      >
                        <span>{tfOpt === "True" ? "✅" : "❌"}</span>
                        <span>{tfOpt} ({tfOpt === "True" ? "To'g'ri" : "Noto'g'ri"})</span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* 3. Fill in the Blanks & Short Answer (Text Input) */}
              {(qType === "fill_blank" || qType === "short_answer" || (!q.options || q.options.length === 0)) && (
                <div className="pt-1">
                  <input
                    type="text"
                    value={answers[q.id] || ""}
                    onChange={(e) => selectAnswer(q.id, e.target.value)}
                    placeholder={qType === "fill_blank" ? "Bo'sh joyga mos so'zni yozing..." : "Javobingizni bu yerga yozing..."}
                    className="w-full px-4 py-3 bg-slate-800/90 border border-slate-700 focus:border-indigo-500 rounded-xl text-xs font-bold text-white outline-none placeholder:text-slate-500 placeholder:font-normal transition shadow-inner"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Spacer to prevent bottom floating bar from covering the last question */}
      <div className="h-28"></div>

      {/* Floating Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#0a0f1d]/90 backdrop-blur-lg p-4 border-t border-slate-800 shadow-2xl max-w-lg mx-auto z-40">
        <button
          onClick={submit}
          disabled={answeredCount < totalQuestions || submitting}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-2xl py-3.5 font-black transition-all disabled:opacity-40 disabled:pointer-events-none shadow-xl shadow-indigo-600/25 text-sm flex items-center justify-center gap-2 active:scale-[0.98]"
        >
          {submitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              {t.submitting}
            </>
          ) : (
            <>
              <span>🚀</span>
              <span>
                {t.submitButton
                  .replace("{answered}", answeredCount)
                  .replace("{total}", totalQuestions)}
              </span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}