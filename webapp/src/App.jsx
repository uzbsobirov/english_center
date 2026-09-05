import { useEffect, useState } from "react";
import WebApp, { setTelegramLanguage } from "./lib/telegram";
import { apiClient } from "./api/client";
import TestPage from "./pages/TestPage";
import TestBuilder from "./pages/TestBuilder";
import AdminDashboard from "./pages/AdminDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import StudentProgress from "./pages/StudentProgress";

function getInitialMode() {
  const params = new URLSearchParams(window.location.search);
  const modeParam = params.get("mode");
  if (modeParam === "admin" || window.location.pathname.includes("admin")) {
    return "admin";
  }
  if (modeParam === "teacher" || window.location.pathname.includes("teacher")) {
    return "teacher";
  }
  if (modeParam === "builder" || window.location.pathname.includes("builder")) {
    return "builder";
  }
  if (modeParam === "progress" || window.location.pathname.includes("progress")) {
    return "progress";
  }
  return "test";
}

function App() {
  const [mode, setMode] = useState(getInitialMode);

  useEffect(() => {
    if (typeof WebApp.ready === "function") {
      WebApp.ready();
      WebApp.expand();
    }

    // Language sync: agar URL da ?lang ko'rsatilmagan bo'lsa, foydalanuvchining bazadagi tilini olib saqlaymiz
    const hasUrlLang = new URLSearchParams(window.location.search).has("lang");
    apiClient
      .get("/api/me")
      .then((res) => {
        if (!hasUrlLang && res.data?.language) {
          setTelegramLanguage(res.data.language);
        }
      })
      .catch(() => {});

    // Role-based check: if teacher opens webapp, ensure they only see TeacherDashboard
    apiClient
      .get("/api/teacher/user-roles")
      .then((res) => {
        if (res.data?.is_teacher && !res.data?.is_admin) {
          setMode("teacher");
        }
      })
      .catch(() => {});
  }, []);

  if (mode === "admin") {
    return <AdminDashboard onSwitchMode={setMode} />;
  }

  if (mode === "teacher") {
    return <TeacherDashboard onSwitchMode={setMode} />;
  }

  if (mode === "builder") {
    return <TestBuilder onSwitchMode={setMode} />;
  }

  if (mode === "progress") {
    return <StudentProgress onSwitchMode={setMode} />;
  }

  return <TestPage onSwitchMode={setMode} />;
}

export default App;