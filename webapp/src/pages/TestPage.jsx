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

function TestPage() {
  const [level, setLevel] = useState(null);
  const [test, setTest] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!level) return;

    setLoading(true);
    setError(null);
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
    const payload = {
      answers: Object.entries(answers).map(([question_id, answer]) => ({
        question_id,
        answer,
      })),
    };

    apiClient
      .post(`/api/tests/${test.id}/submit`, payload)
      .then((res) => setResult(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message));
  };

  if (!level) {
    return <LevelSelect onSelect={setLevel} />;
  }

  if (loading) return <p className="p-4">Yuklanmoqda...</p>;

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <p className="text-red-600 mb-4">Xatolik: {error}</p>
        <button
          onClick={() => {
            setLevel(null);
            setError(null);
          }}
          className="text-blue-600 underline"
        >
          Boshqa darajani tanlash
        </button>
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
      title = "✅ Test topshirildi!";
    } else if (result.outcome === "beginner_recommended") {
      title = "📚 Boshlang'ich kurs tavsiya etiladi";
      body = (
        <p className="text-gray-600">
          Sizga eng boshlang'ich darajadan boshlash tavsiya etiladi.
          Tez orada bizning menejerimiz siz bilan bog'lanib, mos kursni taklif qiladi.
        </p>
      );
    } else if (result.outcome === "try_lower_level") {
      title = "🔄 Pastroq darajani sinab ko'ring";
      body = (
        <p className="text-gray-600">
          Bu daraja uchun hali tayyor emassiz. Pastroq darajadagi testni
          sinab ko'rishni tavsiya qilamiz.
        </p>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow p-6 text-center max-w-sm w-full">
          <h2 className="text-xl font-bold mb-2">{title}</h2>
          {body}
          {result.outcome === "passed" && (
            <p className="text-2xl font-bold mt-2">{result.percent}%</p>
          )}
        </div>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-24">
      <h1 className="text-xl font-bold mb-4">{test.title.uz}</h1>

      <div className="space-y-4">
        {test.questions.map((q, idx) => (
          <div key={q.id} className="bg-white rounded-xl shadow p-4">
            <p className="font-medium mb-3">
              {idx + 1}. {q.text}
            </p>
            <div className="space-y-2">
              {q.options?.map((opt) => (
                <button
                  key={opt}
                  onClick={() => selectAnswer(q.id, opt)}
                  className={`w-full text-left px-3 py-2 rounded-lg border ${
                    answers[q.id] === opt
                      ? "bg-blue-500 text-white border-blue-500"
                      : "bg-white text-gray-700 border-gray-200"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-white p-4 border-t">
        <button
          onClick={submit}
          disabled={answeredCount < test.questions.length}
          className="w-full bg-blue-500 text-white rounded-lg py-3 font-semibold disabled:bg-gray-300"
        >
          Yakunlash ({answeredCount}/{test.questions.length})
        </button>
      </div>
    </div>
  );
}

export default TestPage;