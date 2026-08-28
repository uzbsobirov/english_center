import axios from "axios";
import { getTelegramInitData, getTelegramUser } from "../lib/telegram";

const BASE_URL = import.meta.env.VITE_API_URL || "";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Bypass-Tunnel-Reminder": "true",
  },
});

apiClient.interceptors.request.use((config) => {
  const initData = getTelegramInitData();
  if (initData) {
    config.headers["X-Telegram-Init-Data"] = initData;
  }

  const tgUser = getTelegramUser();
  if (tgUser && tgUser.id) {
    config.headers["X-Telegram-User-Data"] = encodeURIComponent(JSON.stringify(tgUser));
  }

  return config;
});