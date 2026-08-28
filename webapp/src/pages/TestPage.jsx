import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

function LevelSelect({ onSelect }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-xl font-bold mb-6">Darajangizni tanlang</h1>
      <div className="grid grid-cols-2 gap-3 w-full max-w-xs">
        {LEVELS.map((level) => (
          <button
            key={level}
            onClick={() => onSelect(level)}
            className="bg-white shadow rounded-xl py-4 text-lg font-semibold text-gray-700 hover:bg-blue-50 border border-gray-200"
          >
            {level}
          </button>
        ))}
      </div>
    </div>
  );
}

function getInitialLevel() {
  const params = new URLSearchParams(window.location.search);
  const initialLevel = params.get("level");
  if (initialLevel && LEVELS.includes(initialLevel.toUpperCase())) {
    return initialLevel.toUpperCase();
  }
  return null;
}

function TestPage() {
  const [level, setLevel] = useState(getInitialLevel);
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
      .get(`/api/tests/by-level/${level}`)
      .then((res) => setTest(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [level]);

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

  if (!level) {
    return <LevelSelect onSelect={setLevel} />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <p className="text-gray-600 font-medium">Test savollari yuklanmoqda...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4 text-center">
        <div className="bg-white rounded-2xl shadow-sm border p-6 max-w-sm w-full">
          <p className="text-red-500 font-semibold mb-4">⚠️ Xatolik: {error}</p>
          <button
            onClick={() => {
              setLevel(null);
              setError(null);
            }}
            className="w-full bg-blue-600 text-white rounded-xl py-3 font-semibold hover:bg-blue-700 transition"
          >
            Boshqa darajani tanlash
          </button>
        </div>
      </div>
    );
  }

  if (!test) return null;

  if (result) {
    let title = "❌ Test o'tilmadi";
    let body = (
      <p className="text-gray-600">
        {result.score} / {result.total} to'g'ri javob
      </p>
    );

    if (result.outcome === "passed") {
      title = "✅ Test muvaffaqiyatli topshirildi!";
      body = (
        <p className="text-gray-600">
          Tabriklaymiz! Siz <b>{result.score}/{result.total}</b> ({result.percent}%) ball to'pladingiz. Bepul sinov darsi so'rovingiz o'qituvchiga yuborildi.
        </p>
      );
    } else if (result.outcome === "beginner_recommended") {
      title = "📚 Boshlang'ich kurs tavsiya etiladi";
      body = (
        <p className="text-gray-600">
          Sizga boshlang'ich darajadan boshlash tavsiya etiladi. Tez orada menejerimiz siz bilan bog'lanadi.
        </p>
      );
    } else if (result.outcome === "try_lower_level") {
      title = "🔄 Pastroq darajani sinab ko'ring";
      body = (
        <p className="text-gray-600">
          Bu daraja uchun ball yetarli bo'lmadi ({result.percent}%). Pastroq darajadagi testni sinab ko'rishni tavsiya qilamiz.
        </p>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg border p-6 text-center max-w-sm w-full space-y-4">
          <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          {body}
          <button
            onClick={() => {
              setResult(null);
              setAnswers({});
              setLevel(null);
            }}
            className="w-full bg-blue-600 text-white rounded-xl py-3 font-semibold hover:bg-blue-700 transition"
          >
            Yana test ishlash
          </button>
        </div>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;
  const testTitle = typeof test.title === "object" ? (test.title.uz || test.title.en || "Daraja testi") : test.title;

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-28">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-bold text-gray-800">{testTitle}</h1>
        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-1 rounded-full">
          {level}
        </span>
      </div>

      <div className="space-y-4">
        {test.questions.map((q, idx) => (
          <div key={q.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <p className="font-semibold text-gray-800 mb-3">
              <span className="text-blue-600 mr-1">{idx + 1}.</span> {q.text}
            </p>
            <div className="space-y-2">
              {q.options?.map((opt) => {
                const isSelected = answers[q.id] === opt;
                return (
                  <button
                    key={opt}
                    onClick={() => selectAnswer(q.id, opt)}
                    className={`w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition border ${
                      isSelected
                        ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                        : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
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

      <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-md p-4 border-t shadow-lg">
        <button
          onClick={submit}
          disabled={answeredCount < test.questions.length || submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-3.5 font-bold transition disabled:bg-gray-300 disabled:cursor-not-allowed shadow-md"
        >
          {submitting ? "⏳ Natijalar hisoblanmoqda..." : `Yakunlash (${answeredCount}/${test.questions.length})`}
        </button>
      </div>
    </div>
  );
}

export default TestPage;