import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { getTelegramLanguage, setTelegramLanguage } from "../lib/telegram";
import { getTranslation } from "../lib/translations";

const TEST_TYPES_BASE = [
  {
    id: "CEFR",
    badge: "CEFR",
    color: "from-blue-600 to-indigo-600",
  },
  {
    id: "IELTS",
    badge: "IELTS",
    color: "from-purple-600 to-pink-600",
  },
];

const LEVELS = [
  { code: "A1", name: "Beginner", ielts: "Band 3.0-3.5" },
  { code: "A2", name: "Elementary", ielts: "Band 4.0-4.5" },
  { code: "B1", name: "Intermediate", ielts: "Band 5.0-5.5" },
  { code: "B2", name: "Upper-Int.", ielts: "Band 6.0-6.5" },
  { code: "C1", name: "Advanced", ielts: "Band 7.0-8.0" },
  { code: "C2", name: "Proficiency", ielts: "Band 8.5-9.0" },
];

function LanguageSwitcher({ currentLang, onChangeLang }) {
  const languages = [
    { code: "uz", label: "🇺🇿 UZ" },
    { code: "ru", label: "🇷🇺 RU" },
    { code: "en", label: "🇬🇧 EN" },
  ];

  return (
    <div className="flex items-center gap-1 bg-slate-200/70 p-1 rounded-xl shadow-inner text-xs font-bold">
      {languages.map((l) => (
        <button
          key={l.code}
          onClick={() => onChangeLang(l.code)}
          className={`px-2.5 py-1 rounded-lg transition-all ${
            currentLang === l.code
              ? "bg-white text-blue-600 shadow-sm font-extrabold"
              : "text-slate-600 hover:text-slate-900"
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
}) {
  const t = getTranslation(lang);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center p-4 max-w-md mx-auto">
      {/* Top Navbar with Language Switcher */}
      <div className="w-full flex justify-between items-center mt-2 mb-4">
        <span className="text-xs font-extrabold text-blue-600 uppercase tracking-widest">
          ALPHA LC
        </span>
        <LanguageSwitcher currentLang={lang} onChangeLang={onChangeLang} />
      </div>

      {/* Header */}
      <div className="w-full text-center mb-6">
        <h1 className="text-2xl font-black text-slate-800 tracking-tight">
          {t.appTitle}
        </h1>
        <p className="text-slate-500 text-sm mt-1">{t.appSubtitle}</p>
      </div>

      {/* 1-QADAM: Yo'nalish tanlash */}
      <div className="w-full mb-6">
        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          {t.step1Title}
        </label>
        <div className="grid grid-cols-2 gap-3">
          {TEST_TYPES_BASE.map((item) => {
            const isSelected = selectedType === item.id;
            const typeInfo = t.types[item.id] || {};
            return (
              <button
                key={item.id}
                onClick={() => onSelectType(item.id)}
                className={`relative p-4 rounded-2xl text-left transition-all border-2 ${
                  isSelected
                    ? "border-blue-600 bg-white shadow-md ring-2 ring-blue-600/20"
                    : "border-slate-200 bg-white/70 hover:bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                <div className="font-extrabold text-base text-slate-800 mb-1">
                  {typeInfo.title || item.id}
                </div>
                <div className="text-xs text-slate-500 leading-tight">
                  {typeInfo.subtitle || ""}
                </div>
                {isSelected && (
                  <span className="absolute top-2 right-2 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-600"></span>
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 2-QADAM: Daraja tanlash */}
      <div className="w-full">
        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          {t.step2Title.replace("{selectedType}", selectedType)}
        </label>
        <div className="grid grid-cols-2 gap-3">
          {LEVELS.map((lvl) => {
            const lvlDesc = t.levels[lvl.code]?.desc || "";
            return (
              <button
                key={lvl.code}
                onClick={() => onSelectLevel(lvl.code)}
                className="bg-white hover:bg-blue-50/60 active:scale-95 border border-slate-200 hover:border-blue-300 rounded-2xl p-3.5 text-left transition shadow-sm hover:shadow group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-lg font-black text-slate-800 group-hover:text-blue-600 transition">
                    {lvl.code}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                    {selectedType === "IELTS" ? lvl.ielts : lvl.name}
                  </span>
                </div>
                <p className="text-xs text-slate-500">{lvlDesc}</p>
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
  const initialType = params.get("type") || "CEFR";
  const initialLevel = params.get("level");
  return {
    type: initialType.toUpperCase() === "IELTS" ? "IELTS" : "CEFR",
    level:
      initialLevel && LEVELS.some((l) => l.code === initialLevel.toUpperCase())
        ? initialLevel.toUpperCase()
        : null,
  };
}

function TestPage() {
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

  const t = getTranslation(lang);

  const handleLanguageChange = (newLang) => {
    setLang(newLang);
    setTelegramLanguage(newLang);
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
      />
    );
  }

  // 2. Yuklanayotgan holat
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-3"></div>
        <p className="text-slate-600 font-medium text-sm">{t.loading}</p>
      </div>
    );
  }

  // 3. Xatolik holati
  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 text-center">
        <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 max-w-sm w-full">
          <div className="text-3xl mb-2">⚠️</div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">{t.errorTitle}</h2>
          <p className="text-slate-500 text-xs mb-5">{error}</p>
          <button
            onClick={() => {
              setLevel(null);
              setError(null);
            }}
            className="w-full bg-blue-600 text-white rounded-xl py-3 font-bold hover:bg-blue-700 transition"
          >
            {t.changeTest}
          </button>
        </div>
      </div>
    );
  }

  if (!test) return null;

  // 4. Natijalar ekrani
  if (result) {
    const isPassed = result.passed;
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-lg border border-slate-100 p-6 text-center max-w-sm w-full space-y-4">
          <div className="text-4xl mb-1">{isPassed ? "🎉" : "📚"}</div>
          <h2 className="text-xl font-extrabold text-slate-800">
            {isPassed ? t.resultPassedTitle : t.resultFailedTitle}
          </h2>

          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
            <div className="text-3xl font-black text-blue-600 mb-1">
              {result.percent}%
            </div>
            <p className="text-slate-500 text-xs font-semibold">
              {t.correctAnswers
                .replace("{score}", result.score)
                .replace("{total}", result.total)}
            </p>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            {isPassed ? t.resultPassedDesc : t.resultFailedDesc}
          </p>

          <button
            onClick={() => {
              setResult(null);
              setAnswers({});
              setLevel(null);
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-3.5 font-bold transition shadow-md"
          >
            {t.retakeTest}
          </button>
        </div>
      </div>
    );
  }

  // 5. Test savollarini ishlash ekrani
  const answeredCount = Object.keys(answers).length;
  const testTitle =
    typeof test.title === "object"
      ? test.title[lang] || test.title.uz || test.title.en || "Test"
      : test.title;

  return (
    <div className="min-h-screen bg-slate-50 p-4 pb-28 max-w-md mx-auto">
      {/* Test header */}
      <div className="flex items-center justify-between mb-4 sticky top-0 bg-slate-50/90 backdrop-blur py-2 z-10">
        <div>
          <button
            onClick={() => setLevel(null)}
            className="text-xs text-blue-600 font-bold hover:underline mb-0.5 inline-block"
          >
            {t.back}
          </button>
          <h1 className="text-base font-bold text-slate-800 leading-tight">
            {testTitle}
          </h1>
        </div>
        <div className="flex items-center gap-1.5">
          <LanguageSwitcher currentLang={lang} onChangeLang={handleLanguageChange} />
          <span className="bg-blue-100 text-blue-800 text-[11px] font-extrabold px-2.5 py-1 rounded-lg">
            {level}
          </span>
        </div>
      </div>

      {/* Savollar ro'yxati */}
      <div className="space-y-4">
        {test.questions.map((q, idx) => (
          <div
            key={q.id}
            className="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-4 transition"
          >
            <p className="font-semibold text-slate-800 mb-3 text-sm leading-snug">
              <span className="text-blue-600 font-bold mr-1">{idx + 1}.</span>{" "}
              {q.text}
            </p>
            <div className="space-y-2">
              {q.options?.map((opt) => {
                const isSelected = answers[q.id] === opt;
                return (
                  <button
                    key={opt}
                    onClick={() => selectAnswer(q.id, opt)}
                    className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-semibold transition border ${
                      isSelected
                        ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Yakunlash tugmasi */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md p-4 border-t border-slate-200 shadow-lg max-w-md mx-auto">
        <button
          onClick={submit}
          disabled={answeredCount < test.questions.length || submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-3.5 font-bold transition disabled:bg-slate-300 disabled:cursor-not-allowed shadow-md text-sm"
        >
          {submitting
            ? t.submitting
            : t.submitButton
                .replace("{answered}", answeredCount)
                .replace("{total}", test.questions.length)}
        </button>
      </div>
    </div>
  );
}

export default TestPage;