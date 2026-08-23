import { useEffect } from "react";
import WebApp from "./lib/telegram";
import TestPage from "./pages/TestPage";

function App() {
  useEffect(() => {
    if (typeof WebApp.ready === "function") {
      WebApp.ready();
      WebApp.expand();
    }
  }, []);

  return <TestPage />;
}

export default App;