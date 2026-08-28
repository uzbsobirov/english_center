import { useState } from "react";
import { apiClient } from "../api/client";

function TestBuilder() {
  const [file, setFile] = useState(null);
  const [level, setLevel] = useState("B1");
  const [certType, setCertType] = useState("IELTS");
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [reviewedWarnings, setReviewedWarnings] = useState({});
  const [saveStatus, setSaveStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("certificate_type", certType);
    formData.append("level", level);

    try {
      const res = await apiClient.post("/api/teacher/generate-test-from-pdf", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setQuestions(res.data.questions || []);
      setReviewedWarnings({});
    } catch (err) {
      setError(err.response?.data?.detail || "Faylni generatsiya qilishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const toggleReviewWarning = (qId) => {
    setReviewedWarnings((prev) => ({
      ...prev,
      [qId]: !prev[qId],
    }));
  };

  const unreviewedWarningsCount = questions.filter(
    (q) => q.needs_review && !reviewedWarnings[q.id]
  ).length;

  const handleSaveTest = async () => {
    if (unreviewedWarningsCount > 0) {
      alert("⚠️ Iltimos, barcha ogohlantirish belgisi bor savollarni ko'rib chiqing!");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload = {
        certificate_type: certType,
        level: level,
        title: { uz: `${certType} ${level} Test (AI Generatsiya)`, ru: `${certType} ${level} Тест`, en: `${certType} ${level} Test` },
        passing_score: 70.0,
        time_limit_min: 20,
        source: "ai_pdf",
        questions: questions.map((q) => ({
          order_num: q.order_num,
          type: q.type,
          question: q.text,
          options: q.options,
          correct_answer: q.correct_answer,
          points: q.points || 1,
          ai_generated: true,
          needs_review: false, // O'qituvchi tasdiqlaganidan keyin review yechiladi
        })),
      };

      const res = await apiClient.post("/api/teacher/save-test", payload);
      setSaveStatus(res.data.message || "Test muvaffaqiyatli saqlandi!");
    } catch (err) {
      setError(err.response?.data?.detail || "Testni saqlashda xatolik");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-24 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">📄 AI Test Yaratish (PDF)</h1>
      <p className="text-sm text-gray-600 mb-6">
        PDF test faylini yuklang. AI savollarni ajratib oladi va xatoliklarni self-check bilan tekshiradi (TZ 7.5.1).
      </p>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="bg-white rounded-xl shadow p-5 mb-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yo'nalish:</label>
            <select
              value={certType}
              onChange={(e) => setCertType(e.target.value)}
              className="w-full border rounded-lg p-2.5 bg-gray-50"
            >
              <option value="IELTS">IELTS</option>
              <option value="CEFR">CEFR</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Daraja:</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="w-full border rounded-lg p-2.5 bg-gray-50"
            >
              {["A1", "A2", "B1", "B2", "C1", "C2"].map((lvl) => (
                <option key={lvl} value={lvl}>{lvl}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">PDF Fayl tanlang:</label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full border rounded-lg p-2 bg-gray-50"
          />
        </div>

        <button
          type="submit"
          disabled={!file || loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg disabled:bg-gray-300 transition"
        >
          {loading ? "AI Savollarni tahlil qilmoqda..." : "✨ AI orqali generatsiya qilish"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-xl mb-4 border border-red-200">
          {error}
        </div>
      )}

      {saveStatus && (
        <div className="bg-green-50 text-green-700 p-4 rounded-xl mb-4 border border-green-200 font-medium">
          ✅ {saveStatus}
        </div>
      )}

      {/* Questions Preview */}
      {questions.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">
              Savollar Preview ({questions.length} ta)
            </h2>
            {unreviewedWarningsCount > 0 && (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-1 rounded-full border border-amber-300">
                ⚠️ {unreviewedWarningsCount} ta ko'rib chiqish shart
              </span>
            )}
          </div>

          {questions.map((q, idx) => {
            const isWarning = q.needs_review && !reviewedWarnings[q.id];
            return (
              <div
                key={q.id}
                className={`bg-white rounded-xl shadow p-4 border transition ${
                  isWarning ? "border-amber-400 bg-amber-50/30" : "border-gray-200"
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="font-semibold text-gray-800">
                    {idx + 1}. {q.text}
                  </span>
                  {q.needs_review && (
                    <button
                      onClick={() => toggleReviewWarning(q.id)}
                      className={`text-xs px-2 py-1 rounded-md font-medium border ${
                        reviewedWarnings[q.id]
                          ? "bg-green-100 text-green-700 border-green-300"
                          : "bg-amber-100 text-amber-700 border-amber-300"
                      }`}
                    >
                      {reviewedWarnings[q.id] ? "✅ Tasdiqlandi" : "⚠️ Ko'rib chiqish"}
                    </button>
                  )}
                </div>

                {q.options && (
                  <div className="space-y-1 my-2 pl-2">
                    {q.options.map((opt, oIdx) => (
                      <p key={oIdx} className="text-sm text-gray-600">{opt}</p>
                    ))}
                  </div>
                )}

                <div className="mt-2 text-xs text-gray-500">
                  To'g'ri javob: <span className="font-semibold text-gray-700">{q.correct_answer}</span>
                </div>
              </div>
            );
          })}

          {/* Sticky Bottom Action */}
          <div className="fixed bottom-0 left-0 right-0 bg-white p-4 border-t shadow-lg max-w-2xl mx-auto">
            <button
              onClick={handleSaveTest}
              disabled={unreviewedWarningsCount > 0 || loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 rounded-xl disabled:bg-gray-300 transition"
            >
              {unreviewedWarningsCount > 0
                ? `⚠️ Barcha ogohlantirishlarni ko'ring (${unreviewedWarningsCount} ta qoldi)`
                : "🚀 Testni Saqlash va Faollashtirish"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default TestBuilder;
