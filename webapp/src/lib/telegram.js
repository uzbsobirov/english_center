/**
 * Telegram WebApp ob'ektiga dinamik va xavfsiz ulanish.
 * Telegram initData va user ma'lumotlarini barcha manbalardan oladi.
 */

// 1. Dastlabki initData'ni qidirish
const extractInitData = () => {
  // A. Telegram WebApp SDK dan
  if (window.Telegram?.WebApp?.initData) {
    sessionStorage.setItem("tg_init_data", window.Telegram.WebApp.initData);
    return window.Telegram.WebApp.initData;
  }

  // B. URL Hash dan (#tgWebAppData=...)
  if (window.location.hash) {
    try {
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      const tgData = params.get("tgWebAppData");
      if (tgData) {
        sessionStorage.setItem("tg_init_data", tgData);
        return tgData;
      }
    } catch (e) {
      console.warn("Hash parse error:", e);
    }
  }

  // C. URL Query dan (?tgWebAppData=...)
  try {
    const searchParams = new URLSearchParams(window.location.search);
    const tgQueryData = searchParams.get("tgWebAppData");
    if (tgQueryData) {
      sessionStorage.setItem("tg_init_data", tgQueryData);
      return tgQueryData;
    }
  } catch (e) {
    console.warn("Search parse error:", e);
  }

  // D. SessionStorage dan (Serveo / redirectdan keyin saqlanib qolgan)
  const cached = sessionStorage.getItem("tg_init_data");
  if (cached) {
    return cached;
  }

  return "";
};

export const getTelegramInitData = () => {
  return extractInitData();
};

export const getTelegramUser = () => {
  // 1. WebApp SDK initDataUnsafe (Haqiqiy joriy Telegram foydalanuvchisi - 1-darajali ustuvorlik)
  const sdkUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
  if (sdkUser && sdkUser.id) {
    sessionStorage.setItem("tg_user", JSON.stringify(sdkUser));
    return sdkUser;
  }

  // 2. initData string ichidan parse qilish
  const initDataStr = extractInitData();
  if (initDataStr) {
    try {
      const params = new URLSearchParams(initDataStr);
      const userRaw = params.get("user");
      if (userRaw) {
        const u = JSON.parse(userRaw);
        if (u && u.id) {
          sessionStorage.setItem("tg_user", JSON.stringify(u));
          return u;
        }
      }
    } catch (e) {
      console.warn("InitData user parse error:", e);
    }
  }

  // 3. URL search params (?user_id=123&name=Ali&username=alivali)
  try {
    const searchParams = new URLSearchParams(window.location.search);
    const userId = searchParams.get("user_id");
    if (userId && parseInt(userId, 10) > 0) {
      const u = {
        id: parseInt(userId, 10),
        first_name: searchParams.get("name") || "O'quvchi",
        username: searchParams.get("username") || "",
      };
      sessionStorage.setItem("tg_user", JSON.stringify(u));
      return u;
    }
  } catch (e) {
    console.warn("Search params user parse error:", e);
  }

  // 4. SessionStorage dan fallback
  try {
    const cachedUser = sessionStorage.getItem("tg_user");
    if (cachedUser) {
      return JSON.parse(cachedUser);
    }
  } catch (e) {
    console.warn("Cached user parse error:", e);
  }

  return null;
};

export const getTelegramLanguage = () => {
  // 1. URL search params (?lang=uz|ru|en)
  try {
    const searchParams = new URLSearchParams(window.location.search);
    const lang = searchParams.get("lang");
    if (lang && ["uz", "ru", "en"].includes(lang.toLowerCase())) {
      const l = lang.toLowerCase();
      setTelegramLanguage(l);
      return l;
    }
  } catch (e) {
    console.warn("Search params lang parse error:", e);
  }

  // 2. Storage (localStorage yoki sessionStorage)
  try {
    const stored = localStorage.getItem("app_lang") || sessionStorage.getItem("tg_lang");
    if (stored && ["uz", "ru", "en"].includes(stored)) {
      return stored;
    }
  } catch (e) {
    console.warn("Storage lang error:", e);
  }

  // 3. WebApp SDK user language_code
  try {
    const sdkLang = window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code;
    if (sdkLang) {
      const code = sdkLang.slice(0, 2).toLowerCase();
      if (["uz", "ru", "en"].includes(code)) {
        setTelegramLanguage(code);
        return code;
      }
    }
  } catch (e) {
    console.warn("SDK lang parse error:", e);
  }

  return "uz";
};

export const setTelegramLanguage = (lang) => {
  if (["uz", "ru", "en"].includes(lang)) {
    try {
      localStorage.setItem("app_lang", lang);
    } catch (e) {}
    try {
      sessionStorage.setItem("tg_lang", lang);
    } catch (e) {}
  }
};

export const syncUserLanguage = async (lang) => {
  if (!["uz", "ru", "en"].includes(lang)) return;
  setTelegramLanguage(lang);
  try {
    const initData = getTelegramInitData();
    const tgUser = getTelegramUser();
    const headers = {
      "Content-Type": "application/json",
      "Bypass-Tunnel-Reminder": "true",
    };
    if (initData) headers["X-Telegram-Init-Data"] = initData;
    if (tgUser && tgUser.id) {
      headers["X-Telegram-User-Data"] = encodeURIComponent(JSON.stringify(tgUser));
    }

    const userQuery = tgUser && tgUser.id ? `?user_id=${tgUser.id}` : "";
    await fetch(`/api/user/language${userQuery}`, {
      method: "POST",
      headers,
      body: JSON.stringify({ language: lang }),
    });
  } catch (err) {
    console.warn("syncUserLanguage error:", err);
  }
};

export const getTelegramWebApp = () => {
  return window.Telegram?.WebApp || null;
};

const WebAppProxy = new Proxy({}, {
  get(target, prop) {
    const webApp = window.Telegram?.WebApp;
    if (webApp && prop in webApp) {
      const val = webApp[prop];
      return typeof val === "function" ? val.bind(webApp) : val;
    }
    if (prop === "initData") {
      return getTelegramInitData();
    }
    if (prop === "initDataUnsafe") {
      return { user: getTelegramUser(), language: getTelegramLanguage() };
    }
    if (prop === "ready" || prop === "expand" || prop === "close") {
      return () => {};
    }
    return undefined;
  }
});

export default WebAppProxy;