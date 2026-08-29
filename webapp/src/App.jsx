import { useEffect, useState } from "react";
import WebApp from "./lib/telegram";
import TestPage from "./pages/TestPage";
import TestBuilder from "./pages/TestBuilder";
import AdminDashboard from "./pages/AdminDashboard";

function getInitialMode() {
  const params = new URLSearchParams(window.location.search);
  const modeParam = params.get("mode");
  if (modeParam === "admin" || window.location.pathname.includes("admin")) {
    return "admin";
  }
  if (modeParam === "teacher" || window.location.pathname.includes("builder")) {
    return "teacher";
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
  }, []);

  if (mode === "admin") {
    return <AdminDashboard onSwitchMode={setMode} />;
  }

  if (mode === "teacher") {
    return <TestBuilder onSwitchMode={setMode} />;
  }

  return <TestPage onSwitchMode={setMode} />;
}

export default App;