import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

const TEST_TYPES = [
  {
    id: "CEFR",
    title: "🎯 CEFR Testlari",
    subtitle: "Grammatika va leksika darajasi",
    badge: "CEFR",
    color: "from-blue-600 to-indigo-600",
  },
  {
    id: "IELTS",
    title: "🇬🇧 IELTS Testlari",
    subtitle: "Academic & General tayyorgarlik",
    badge: "IELTS",
    color: "from-purple-600 to-pink-600",
  },
];

const LEVELS = [
  { code: "A1", name: "Beginner", ielts: "Band 3.0-3.5", desc: "Boshlang'ich daraja" },
  { code: "A2", name: "Elementary", ielts: "Band 4.0-4.5", desc: "Oddiy muloqot" },
  { code: "B1", name: "Intermediate", ielts: "Band 5.0-5.5", desc: "O'rta daraja" },
  { code: "B2", name: "Upper-Int.", ielts: "Band 6.0-6.5", desc: "Kuchli o'rta" },
  { code: "C1", name: "Advanced", ielts: "Band 7.0-8.0", desc: "Yuqori daraja" },
  { code: "C2", name: "Proficiency", ielts: "Band 8.5-9.0", desc: "Mukammal" },
];

function CategoryAndLevelSelect({ selectedType, onSelectType, onSelectLevel }) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center p-4 max-w-md mx-auto">
      {/* Header */}
      <div className="w-full text-center mt-4 mb-6">
        <h1 className="text-2xl font-black text-slate-800 tracking-tight">Ingliz Tili Testlari</h1>
        <p className="text-slate-500 text-sm mt-1">Yo'nalish va darajangizni tanlang</p>
      </div>

      {/* 1-QADAM: Yo'nalish tanlash */}
      <div className="w-full mb-6">
        <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          1. Yo'nalishni tanlang:
        </label>
        <div className="grid grid-cols-2 gap-3">
          {TEST_TYPES.map((t) => {
            const isSelected = selectedType === t.id;
            return (
              <button
                key={t.id}
                onClick={() => onSelectType(t.id)}
                className={`relative p-4 rounded-2xl text-left transition-all border-2 ${
                  isSelected
                    ? "border-blue-600 bg-white shadow-md ring-2 ring-blue-600/20"
                    : "border-slate-200 bg-white/70 hover:bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                <div className="font-extrabold text-base text-slate-800 mb-1">{t.title}</div>
                <div className="text-xs text-slate-500 leading-tight">{t.subtitle}</div>
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
          2. Darajani tanlang ({selectedType}):
        </label>
        <div className="grid grid-cols-2 gap-3">
          {LEVELS.map((lvl) => (
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
              <p className="text-xs text-slate-500">{lvl.desc}</p>
            </button>
          ))}
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
    level: initialLevel && LEVELS.some((l) => l.code === initialLevel.toUpperCase()) ? initialLevel.toUpperCase() : null,
  };
}

function TestPage() {
  const [initialParams] = useState(getInitialParams);
  const [selectedType, setSelectedType] = useState(initialParams.type);
  const [level, setLevel] = useState(initialParams.level);
  const [test, setTest] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

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
        <p className="text-slate-600 font-medium text-sm">Test savollari yuklanmoqda...</p>
      </div>
    );
  }

  // 3. Xatolik holati
  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 text-center">
        <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 max-w-sm w-full">
          <div className="text-3xl mb-2">⚠️</div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">Test yuklanmadi</h2>
          <p className="text-slate-500 text-xs mb-5">{error}</p>
          <button
            onClick={() => {
              setLevel(null);
              setError(null);
            }}
            className="w-full bg-blue-600 text-white rounded-xl py-3 font-bold hover:bg-blue-700 transition"
          >
            Boshqa test tanlash
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
            {isPassed ? "Ajoyib natija!" : "Test yakunlandi"}
          </h2>

          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
            <div className="text-3xl font-black text-blue-600 mb-1">
              {result.percent}%
            </div>
            <p className="text-slate-500 text-xs font-semibold">
              {result.score} / {result.total} ta to'g'ri javob
            </p>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            {isPassed
              ? "Tabriklaymiz! Siz o'tish balini to'pladingiz. Natijangiz Telegram botingizga yuborildi."
              : "Bu daraja uchun ball yetarli bo'lmadi. Bilimingizni mustahkamlab, qayta urinib ko'rishingiz mumkin."}
          </p>

          <button
            onClick={() => {
              setResult(null);
              setAnswers({});
              setLevel(null);
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-3.5 font-bold transition shadow-md"
          >
            Yana test ishlash
          </button>
        </div>
      </div>
    );
  }

  // 5. Test savollarini ishlash ekrani
  const answeredCount = Object.keys(answers).length;
  const testTitle =
    typeof test.title === "object"
      ? test.title.uz || test.title.en || "Daraja testi"
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
            ◀️ Orqaga
          </button>
          <h1 className="text-base font-bold text-slate-800 leading-tight">{testTitle}</h1>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="bg-purple-100 text-purple-800 text-[11px] font-extrabold px-2.5 py-1 rounded-lg">
            {test.certificate_type || selectedType}
          </span>
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
              <span className="text-blue-600 font-bold mr-1">{idx + 1}.</span> {q.text}
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
            ? "⏳ Natijalar hisoblanmoqda..."
            : `Yakunlash (${answeredCount}/${test.questions.length})`}
        </button>
      </div>
    </div>
  );
}

export default TestPage;