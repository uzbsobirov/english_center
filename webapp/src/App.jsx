import { useEffect, useState } from "react";
import WebApp from "./lib/telegram";
import TestPage from "./pages/TestPage";
import TestBuilder from "./pages/TestBuilder";

function getInitialMode() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("mode") === "teacher" || window.location.pathname.includes("builder")) {
    return "teacher";
  }
  return "test";
}

function App() {
  const [mode] = useState(getInitialMode);

  useEffect(() => {
    if (typeof WebApp.ready === "function") {
      WebApp.ready();
      WebApp.expand();
    }
  }, []);

  return mode === "teacher" ? <TestBuilder /> : <TestPage />;
}

export default App;