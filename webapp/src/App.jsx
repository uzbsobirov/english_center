import { useEffect, useState } from "react";
import WebApp from "./lib/telegram";
import { apiClient } from "./api/client";

function App() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (typeof WebApp.ready === "function") {
      WebApp.ready();
      WebApp.expand();
    }

    apiClient
      .get("/api/me")
      .then((res) => setUser(res.data.telegram_user))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-bold mb-4">English Center</h1>

      {error && <p className="text-red-600">Xatolik: {error}</p>}

      {user ? (
        <div className="bg-white rounded-xl shadow p-4 text-center">
          <p className="text-lg font-semibold">Salom, {user.first_name}!</p>
          <p className="text-gray-500 text-sm">Telegram ID: {user.id}</p>
          <p className="text-green-600 mt-2">✅ Backend bilan bog'lanish ishlayapti</p>
        </div>
      ) : (
        !error && <p>Yuklanmoqda...</p>
      )}
    </div>
  );
}

export default App;