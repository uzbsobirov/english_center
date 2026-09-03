import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

export default function TestBuilder({ onSwitchMode }) {
  const [activeTab, setActiveTab] = useState("builder"); // 'builder' | 'list'
  const [existingTests, setExistingTests] = useState([]);
  const [loadingTests, setLoadingTests] = useState(false);
  const [editingTestId, setEditingTestId] = useState(null);

  // Form states
  const [file, setFile] = useState(null);
  const [level, setLevel] = useState("B1");
  const [certType, setCertType] = useState("IELTS");
  const [titleUz, setTitleUz] = useState("");
  const [passingScore, setPassingScore] = useState(70);
  const [timeLimitMin, setTimeLimitMin] = useState(15);
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [reviewedWarnings, setReviewedWarnings] = useState({});
  const [saveStatus, setSaveStatus] = useState(null);
  const [error, setError] = useState(null);

  const fetchExistingTests = async () => {
    setLoadingTests(true);
    try {
      const res = await apiClient.get("/api/teacher/tests");
      setExistingTests(res.data || []);
    } catch (err) {
      console.error("Testlarni yuklashda xatolik:", err);
    } finally {
      setLoadingTests(false);
    }
  };

  useEffect(() => {
    fetchExistingTests();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setSaveStatus(null);
    setEditingTestId(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("certificate_type", certType);
    formData.append("level", level);

    try {
      const res = await apiClient.post("/api/teacher/generate-test-from-pdf", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const generated = res.data.questions || [];
      setQuestions(generated);
      setTitleUz(`${certType} ${level} — AI Generatsiya Testi`);
      setReviewedWarnings({});
    } catch (err) {
      setError(err.response?.data?.detail || "PDF faylini tahlil qilishda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTestToEdit = async (testId) => {
    setLoading(true);
    setError(null);
    setSaveStatus(null);
    try {
      const res = await apiClient.get(`/api/teacher/tests/${testId}`);
      const tData = res.data;
      setEditingTestId(testId);
      setCertType(tData.certificate_type || "IELTS");
      setLevel(tData.level || "B1");
      setTitleUz(tData.title_uz || tData.title?.uz || "");
      setPassingScore(tData.passing_score || 70);
      setTimeLimitMin(tData.time_limit_min || 15);
      setQuestions(tData.questions || []);
      setReviewedWarnings({});
      setActiveTab("builder");
    } catch (err) {
      setError(err.response?.data?.detail || "Test ma'lumotlarini yuklashda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewManualTest = () => {
    setEditingTestId(null);
    setFile(null);
    setTitleUz(`${certType} ${level} Yangi Test`);
    setQuestions([
      {
        id: `q_1`,
        order_num: 1,
        type: "mcq",
        text: "Savol matnini bu yerga yozing...",
        options: ["A) 1-variant", "B) 2-variant", "C) 3-variant", "D) 4-variant"],
        correct_answer: "A) 1-variant",
        points: 1,
        ai_generated: false,
        needs_review: false,
      },
    ]);
    setSaveStatus(null);
    setError(null);
    setActiveTab("builder");
  };

  const toggleReviewWarning = (qId) => {
    setReviewedWarnings((prev) => ({
      ...prev,
      [qId]: !prev[qId],
    }));
  };

  const handleQuestionTypeChange = (idx, newType) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const current = updated[idx];
      let options = current.options || [];
      let correct_answer = current.correct_answer || "";

      if (newType === "mcq") {
        if (!options || options.length < 2) {
          options = ["A) Variant 1", "B) Variant 2", "C) Variant 3", "D) Variant 4"];
        }
        if (!correct_answer || !options.includes(correct_answer)) {
          correct_answer = options[0];
        }
      } else if (newType === "true_false") {
        options = ["True", "False"];
        correct_answer = ["True", "False"].includes(correct_answer) ? correct_answer : "True";
      } else if (newType === "fill_blank" || newType === "short_answer") {
        options = [];
        if (correct_answer.startsWith("A)") || correct_answer.startsWith("B)")) {
          correct_answer = correct_answer.replace(/^[A-Ea-e][\)\.\:\-\s]+/, "").trim();
        }
      }

      updated[idx] = {
        ...current,
        type: newType,
        options,
        correct_answer,
        needs_review: false,
      };
      return updated;
    });
  };

  const handleQuestionTextChange = (idx, newText) => {
    setQuestions((prev) => {
      const updated = [...prev];
      updated[idx] = { ...updated[idx], text: newText };
      return updated;
    });
  };

  const handleOptionChange = (qIdx, optIdx, newOptText) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const newOptions = [...(updated[qIdx].options || [])];
      const oldOpt = newOptions[optIdx];
      newOptions[optIdx] = newOptText;
      let newCorrect = updated[qIdx].correct_answer;
      if (newCorrect === oldOpt) {
        newCorrect = newOptText;
      }
      updated[qIdx] = { ...updated[qIdx], options: newOptions, correct_answer: newCorrect };
      return updated;
    });
  };

  const handleAddOption = (qIdx) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const currentOpts = updated[qIdx].options || [];
      const nextLetter = String.fromCharCode(65 + currentOpts.length);
      const newOpts = [...currentOpts, `${nextLetter}) Yangi variant`];
      updated[qIdx] = { ...updated[qIdx], options: newOpts };
      return updated;
    });
  };

  const handleDeleteOption = (qIdx, optIdx) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const currentOpts = updated[qIdx].options || [];
      if (currentOpts.length <= 2) {
        alert("Kamida 2 ta variant bo'lishi kerak!");
        return prev;
      }
      const removedOpt = currentOpts[optIdx];
      const newOpts = currentOpts.filter((_, i) => i !== optIdx);
      let newCorrect = updated[qIdx].correct_answer;
      if (newCorrect === removedOpt) {
        newCorrect = newOpts[0];
      }
      updated[qIdx] = { ...updated[qIdx], options: newOpts, correct_answer: newCorrect };
      return updated;
    });
  };

  const handleSelectCorrectAnswer = (qIdx, correctAns) => {
    setQuestions((prev) => {
      const updated = [...prev];
      updated[qIdx] = { ...updated[qIdx], correct_answer: correctAns };
      return updated;
    });
  };

  const handleDeleteQuestion = (idx) => {
    setQuestions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAddQuestion = (type = "mcq") => {
    const nextId = `q_custom_${Date.now()}`;
    let defaultOpts = [];
    let defaultCorrect = "";

    if (type === "mcq") {
      defaultOpts = ["A) Variant 1", "B) Variant 2", "C) Variant 3", "D) Variant 4"];
      defaultCorrect = "A) Variant 1";
    } else if (type === "true_false") {
      defaultOpts = ["True", "False"];
      defaultCorrect = "True";
    }

    setQuestions((prev) => [
      ...prev,
      {
        id: nextId,
        order_num: prev.length + 1,
        type: type,
        text: type === "fill_blank" ? "Gapdagi bo'sh joyni to'ldiring: She _____ yesterday." : "Yangi savol matni...",
        options: defaultOpts,
        correct_answer: defaultCorrect,
        points: 1,
        ai_generated: false,
        needs_review: false,
      },
    ]);
  };

  const unreviewedWarningsCount = questions.filter(
    (q) => q.needs_review && !reviewedWarnings[q.id]
  ).length;

  const handleSaveTest = async () => {
    if (unreviewedWarningsCount > 0) {
      alert("⚠️ Iltimos, barcha ogohlantirish belgisi bor savollarni tekshiring va tasdiqlang!");
      return;
    }

    if (questions.length === 0) {
      alert("Testda kamida 1 ta savol bo'lishi kerak!");
      return;
    }

    // Har bir savolda to'g'ri javob kiritilganligini tekshirish
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i];
      if (!q.text || !q.text.trim()) {
        alert(`⚠️ #${i + 1}-savol matni bo'sh bo'lishi mumkin emas!`);
        return;
      }
      if (!q.correct_answer || !q.correct_answer.trim()) {
        alert(`⚠️ #${i + 1}-savol uchun to'g'ri javob kiritilmagan!`);
        return;
      }
    }

    setLoading(true);
    setError(null);
    try {
      const payload = {
        certificate_type: certType,
        level: level,
        title: {
          uz: titleUz || `${certType} ${level} Test`,
          ru: `${certType} ${level} Тест`,
          en: `${certType} ${level} Test`,
        },
        passing_score: Number(passingScore) || 70.0,
        time_limit_min: Number(timeLimitMin) || 15,
        source: editingTestId ? "manual" : "ai_pdf",
        questions: questions.map((q, idx) => ({
          order_num: idx + 1,
          type: q.type || "mcq",
          question: q.text,
          text: q.text,
          options: q.options || [],
          correct_answer: q.correct_answer,
          points: q.points || 1,
          ai_generated: q.ai_generated || false,
          needs_review: false,
        })),
      };

      if (editingTestId) {
        const res = await apiClient.put(`/api/teacher/tests/${editingTestId}`, payload);
        setSaveStatus(res.data.message || "Test muvaffaqiyatli yangilandi!");
      } else {
        const res = await apiClient.post("/api/teacher/save-test", payload);
        setSaveStatus(res.data.message || "Test muvaffaqiyatli saqlandi va faollashtirildi! O'quvchilar ishlashiga tayyor.");
      }
      fetchExistingTests();
    } catch (err) {
      setError(err.response?.data?.detail || "Testni saqlashda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 p-4 pb-32 max-w-4xl mx-auto font-sans relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute top-0 left-1/3 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-10 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-4 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl shadow-lg shadow-indigo-500/25">
            🛠
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-black text-white leading-tight">
              Test Builder & Boshqaruv
            </h1>
            <p className="text-xs text-slate-400">
              PDF yuklash, AI orqali savollar yaratish va mavjud testlarni tahrirlash
            </p>
          </div>
        </div>

        {onSwitchMode && (
          <button
            onClick={() => onSwitchMode("admin")}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-xl border border-slate-700 transition active:scale-95 flex items-center gap-1.5"
          >
            <span>⬅️</span>
            <span className="hidden sm:inline">Admin Panel</span>
          </button>
        )}
      </div>

      {/* Mode Tabs */}
      <div className="flex items-center gap-2 mb-6 border-b border-slate-800 pb-2">
        <button
          onClick={() => {
            setActiveTab("builder");
            setSaveStatus(null);
          }}
          className={`px-4 py-2 rounded-xl text-xs font-black transition flex items-center gap-1.5 ${
            activeTab === "builder"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
              : "bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800"
          }`}
        >
          <span>🤖</span>
          <span>{editingTestId ? `✏️ Tahrirlash (#${editingTestId})` : "Yangi Test Yaratish"}</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("list");
            fetchExistingTests();
          }}
          className={`px-4 py-2 rounded-xl text-xs font-black transition flex items-center gap-1.5 ${
            activeTab === "list"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
              : "bg-slate-900/80 text-slate-400 hover:text-white border border-slate-800"
          }`}
        >
          <span>📚</span>
          <span>Mavjud Testlar Ro'yxati ({existingTests.length})</span>
        </button>
      </div>

      {/* TAB 1: BUILDER & EDITOR */}
      {activeTab === "builder" && (
        <div className="space-y-6 relative z-10">
          {/* Success Banner */}
          {saveStatus && (
            <div className="p-5 rounded-3xl bg-emerald-500/15 border-2 border-emerald-500/40 text-emerald-300 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-3 animate-bounce-once">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🎉</span>
                <div>
                  <h4 className="font-black text-sm text-emerald-200">Muvaffaqiyatli saqlandi!</h4>
                  <p className="text-xs text-emerald-300/90">{saveStatus}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setActiveTab("list");
                  fetchExistingTests();
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs rounded-xl shadow-md transition"
              >
                Ro'yxatda ko'rish →
              </button>
            </div>
          )}

          {error && (
            <div className="glass-panel border border-red-500/30 text-red-300 p-4 rounded-2xl text-xs flex items-center justify-between shadow-xl">
              <span>⚠️ {error}</span>
              <button onClick={() => setError(null)} className="underline font-black">
                Yopish
              </button>
            </div>
          )}

          {/* Top Form Settings */}
          <div className="glass-panel p-6 rounded-3xl border border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-black text-white flex items-center gap-2">
                <span>⚙️</span> 1. Test Asosiy Parametrlari
              </h2>
              {editingTestId && (
                <span className="text-[10px] font-black px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  Tahrirlash rejimi: Test #{editingTestId}
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  🎯 Yo'nalish:
                </label>
                <select
                  value={certType}
                  onChange={(e) => setCertType(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs font-bold text-white outline-none focus:border-indigo-500"
                >
                  <option value="IELTS">IELTS</option>
                  <option value="CEFR">CEFR</option>
                  <option value="General">General English</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  📊 Daraja:
                </label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs font-bold text-white outline-none focus:border-indigo-500"
                >
                  {["A1", "A2", "B1", "B2", "C1", "C2"].map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  🏆 O'tish bali (%):
                </label>
                <input
                  type="number"
                  min="10"
                  max="100"
                  value={passingScore}
                  onChange={(e) => setPassingScore(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs font-bold text-white outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">
                📝 Test Sarlavhasi (UZ):
              </label>
              <input
                type="text"
                value={titleUz}
                onChange={(e) => setTitleUz(e.target.value)}
                placeholder="Masalan: IELTS B2 Grammar & Reading Mock"
                className="w-full px-3 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs font-bold text-white outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* PDF Upload Box */}
          {!editingTestId && (
            <form onSubmit={handleUpload} className="glass-panel p-6 rounded-3xl border border-slate-800 shadow-2xl space-y-4">
              <h2 className="text-sm font-black text-white flex items-center gap-2">
                <span>📄</span> 2. PDF Faylni Yuklash (AI Tahlili)
              </h2>

              <div className="relative border-2 border-dashed border-indigo-500/40 hover:border-indigo-500 rounded-3xl p-8 text-center bg-slate-900/40 hover:bg-slate-900/60 transition group cursor-pointer">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">📑</div>
                <p className="text-xs font-bold text-white">
                  {file ? `Tanlandi: ${file.name}` : "PDF faylini shu yerga tashlang yoki bosing"}
                </p>
                <p className="text-[10px] text-slate-400 mt-1">
                  Maksimal hajm: 10 MB (.pdf)
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={loading || !file}
                  className="flex-1 py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-black text-xs rounded-2xl shadow-xl shadow-indigo-600/25 transition active:scale-95 disabled:opacity-40 disabled:pointer-events-none flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>AI Tahlil qilmoqda...</span>
                    </>
                  ) : (
                    <>
                      <span>⚡️</span>
                      <span>PDF dan Savollarni Ajratish</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleCreateNewManualTest}
                  className="px-4 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-2xl border border-slate-700 transition"
                >
                  ✍️ Qo'lda Yozish
                </button>
              </div>
            </form>
          )}

          {/* Question List Editor */}
          {questions.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-black text-white flex items-center gap-2">
                  <span>📝</span> Savollar Ro'yxati ({questions.length} ta)
                </h3>

                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    type="button"
                    onClick={() => handleAddQuestion("mcq")}
                    className="px-2.5 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1"
                  >
                    <span>➕</span> 🔘 Variantli
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAddQuestion("true_false")}
                    className="px-2.5 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1"
                  >
                    <span>➕</span> ⚖️ True/False
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAddQuestion("fill_blank")}
                    className="px-2.5 py-1.5 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1"
                  >
                    <span>➕</span> ✍️ Bo'sh joy
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAddQuestion("short_answer")}
                    className="px-2.5 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-bold rounded-xl transition active:scale-95 flex items-center gap-1"
                  >
                    <span>➕</span> 📝 Qisqa javob
                  </button>
                </div>
              </div>

              {unreviewedWarningsCount > 0 && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/30 text-amber-300 rounded-2xl text-xs flex items-center justify-between">
                  <span>⚠️ Diqqat: {unreviewedWarningsCount} ta savolda e'tibor talab qilinadigan nuqta bor.</span>
                </div>
              )}

              {questions.map((q, idx) => {
                const isWarning = q.needs_review && !reviewedWarnings[q.id];
                const qType = q.type || "mcq";

                return (
                  <div
                    key={q.id || idx}
                    className={`glass-panel p-5 rounded-3xl border transition-all ${
                      isWarning
                        ? "border-amber-500/50 bg-amber-950/10 shadow-lg shadow-amber-500/5"
                        : "border-slate-800 shadow-xl"
                    } space-y-3.5`}
                  >
                    {/* Header: Number, Type Selector, Warning & Delete */}
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 font-black text-xs flex items-center justify-center">
                          {idx + 1}
                        </span>

                        {/* Question Type Switcher Pills */}
                        <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-[10px] font-bold">
                          <button
                            type="button"
                            onClick={() => handleQuestionTypeChange(idx, "mcq")}
                            className={`px-2 py-0.5 rounded-lg transition ${
                              qType === "mcq"
                                ? "bg-indigo-600 text-white shadow"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            🔘 Variantli
                          </button>
                          <button
                            type="button"
                            onClick={() => handleQuestionTypeChange(idx, "true_false")}
                            className={`px-2 py-0.5 rounded-lg transition ${
                              qType === "true_false"
                                ? "bg-emerald-600 text-white shadow"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            ⚖️ True/False
                          </button>
                          <button
                            type="button"
                            onClick={() => handleQuestionTypeChange(idx, "fill_blank")}
                            className={`px-2 py-0.5 rounded-lg transition ${
                              qType === "fill_blank"
                                ? "bg-amber-600 text-white shadow"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            ✍️ Bo'sh joy
                          </button>
                          <button
                            type="button"
                            onClick={() => handleQuestionTypeChange(idx, "short_answer")}
                            className={`px-2 py-0.5 rounded-lg transition ${
                              qType === "short_answer"
                                ? "bg-purple-600 text-white shadow"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            📝 Ochiq savol
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {q.needs_review && (
                          <button
                            type="button"
                            onClick={() => toggleReviewWarning(q.id)}
                            className={`px-2.5 py-1 rounded-xl text-[10px] font-black border transition ${
                              reviewedWarnings[q.id]
                                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                                : "bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse"
                            }`}
                          >
                            {reviewedWarnings[q.id] ? "✅ Tasdiqlandi" : "⚠️ Tekshirish kerak"}
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleDeleteQuestion(idx)}
                          className="text-slate-500 hover:text-red-400 text-xs p-1.5 rounded-lg bg-slate-900 hover:bg-red-500/10 transition"
                          title="Savolni o'chirish"
                        >
                          🗑
                        </button>
                      </div>
                    </div>

                    {/* Question text */}
                    <div>
                      <label className="block text-[10px] font-bold text-slate-400 mb-1 uppercase tracking-wider">
                        Savol matni {qType === "fill_blank" ? "(Bo'sh joy uchun '_____' ishlating)" : ""}:
                      </label>
                      <textarea
                        rows={2}
                        value={q.text || ""}
                        onChange={(e) => handleQuestionTextChange(idx, e.target.value)}
                        placeholder="Savol matnini kiriting..."
                        className="w-full p-3 bg-slate-900/80 border border-slate-700/80 rounded-2xl text-xs font-semibold text-white outline-none focus:border-indigo-500"
                      />
                    </div>

                    {/* TYPE 1: MCQ Options list */}
                    {qType === "mcq" && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          <span>Variantlar (To'g'ri javobni tanlang):</span>
                          <button
                            type="button"
                            onClick={() => handleAddOption(idx)}
                            className="text-indigo-400 hover:text-indigo-300 font-black normal-case text-xs flex items-center gap-1"
                          >
                            <span>➕</span> Variant qo'shish
                          </button>
                        </div>
                        {(q.options || []).map((opt, optIdx) => {
                          const isCorrect = q.correct_answer === opt;
                          return (
                            <div
                              key={optIdx}
                              className={`flex items-center gap-2 p-2 rounded-xl border transition ${
                                isCorrect
                                  ? "bg-emerald-500/15 border-emerald-500/40 shadow-sm"
                                  : "bg-slate-900 border-slate-800"
                              }`}
                            >
                              <input
                                type="radio"
                                name={`correct_${q.id || idx}`}
                                checked={isCorrect}
                                onChange={() => handleSelectCorrectAnswer(idx, opt)}
                                className="w-4 h-4 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                                title="To'g'ri javob qilib belgilash"
                              />
                              <input
                                type="text"
                                value={opt}
                                onChange={(e) => handleOptionChange(idx, optIdx, e.target.value)}
                                className="flex-1 bg-transparent border-none text-xs font-semibold text-white outline-none"
                              />
                              {(q.options || []).length > 2 && (
                                <button
                                  type="button"
                                  onClick={() => handleDeleteOption(idx, optIdx)}
                                  className="text-slate-500 hover:text-red-400 text-xs px-1"
                                  title="Variantni o'chirish"
                                >
                                  ✖
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* TYPE 2: True / False Selector */}
                    {qType === "true_false" && (
                      <div className="space-y-2">
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          To'g'ri javobni tanlang:
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          {["True", "False"].map((opt) => {
                            const isSelected = (q.correct_answer || "").toLowerCase() === opt.toLowerCase();
                            return (
                              <button
                                key={opt}
                                type="button"
                                onClick={() => handleSelectCorrectAnswer(idx, opt)}
                                className={`py-3 px-4 rounded-2xl border text-xs font-black transition flex items-center justify-center gap-2 ${
                                  isSelected
                                    ? opt === "True"
                                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-500/20"
                                      : "bg-red-500/20 border-red-500 text-red-300 shadow-md shadow-red-500/20"
                                    : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800"
                                }`}
                              >
                                <span>{opt === "True" ? "✅" : "❌"}</span>
                                <span>{opt} ({opt === "True" ? "To'g'ri" : "Noto'g'ri"})</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* TYPE 3 & 4: Fill Blank & Short Answer (Text Input) */}
                    {(qType === "fill_blank" || qType === "short_answer") && (
                      <div className="space-y-1.5">
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                          <span>To'g'ri javob matni:</span>
                          <span className="text-slate-500 normal-case text-[10px]">
                            Bir nechta to'g'ri variant bo'lsa: <code>/</code> bilan ajrating
                          </span>
                        </div>
                        <input
                          type="text"
                          value={q.correct_answer || ""}
                          onChange={(e) => handleSelectCorrectAnswer(idx, e.target.value)}
                          placeholder="Masalan: went yoki went / had gone"
                          className="w-full px-3 py-2.5 bg-slate-900 border border-emerald-500/40 rounded-xl text-xs font-bold text-emerald-300 outline-none focus:border-emerald-400"
                        />
                        <p className="text-[10px] text-slate-500 italic">
                          ℹ️ O'quvchi kiritgan matn katta-kichik harflaridan qat'iy nazar to'g'ri javobga mos bo'lsa to'liq qabul qilinadi.
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Bottom Action Save Button */}
              <div className="pt-4 sticky bottom-4 z-20">
                <button
                  type="button"
                  onClick={handleSaveTest}
                  disabled={loading}
                  className="w-full py-4 bg-gradient-to-r from-emerald-600 via-teal-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-black text-sm rounded-2xl shadow-2xl shadow-emerald-600/30 transition active:scale-[0.99] flex items-center justify-center gap-2"
                >
                  <span>💾</span>
                  <span>
                    {editingTestId
                      ? `Testni Yangilash (#${editingTestId})`
                      : "Testni Saqlash va Faollashtirish"}
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXISTING TESTS LIST */}
      {activeTab === "list" && (
        <div className="space-y-4 relative z-10">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-black text-white">
              Barcha Testlar Ro'yxati ({existingTests.length})
            </h2>

            <button
              onClick={handleCreateNewManualTest}
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs rounded-xl shadow-md transition active:scale-95 flex items-center gap-1.5"
            >
              <span>➕</span>
              <span>Yangi Test Qo'shish</span>
            </button>
          </div>

          {loadingTests ? (
            <div className="p-8 text-center text-xs text-slate-400 font-bold">
              ⏳ Testlar yuklanmoqda...
            </div>
          ) : existingTests.length === 0 ? (
            <div className="p-8 glass-panel rounded-3xl text-center text-xs text-slate-400 border border-slate-800">
              Hozircha testlar mavjud emas.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {existingTests.map((t) => (
                <div
                  key={t.id}
                  className="glass-panel p-5 rounded-3xl border border-slate-800 hover:border-indigo-500/50 transition-all shadow-xl space-y-3 relative group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-black px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase">
                      {t.certificate_type} • {t.level}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        t.is_active
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-red-500/20 text-red-300"
                      }`}
                    >
                      {t.is_active ? "Faol" : "Nofaol"}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-black text-sm text-white group-hover:text-indigo-300 transition">
                      {t.title_uz || t.title?.uz || "Nomsiz Test"}
                    </h3>
                    <div className="text-xs text-slate-400 mt-1 space-y-1">
                      <div>📝 Savollar soni: <b className="text-slate-200">{t.total_questions} ta</b></div>
                      <div>🏆 O'tish bali: <b className="text-emerald-400">{t.passing_score}%</b></div>
                      <div>⏱ Vaqt chegarasi: <b className="text-slate-300">{t.time_limit_min} daqiqa</b></div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80">
                    <button
                      onClick={() => handleSelectTestToEdit(t.id)}
                      className="w-full py-2 bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white font-black text-xs rounded-xl border border-slate-700 hover:border-indigo-500 transition active:scale-95 flex items-center justify-center gap-1.5"
                    >
                      <span>✏️</span>
                      <span>Savollarni Ko'rish va Tahrirlash</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
