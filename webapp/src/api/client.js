import axios from "axios";
import WebApp from "../lib/telegram";

const BASE_URL = import.meta.env.VITE_API_URL || "";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Bypass-Tunnel-Reminder": "true",
  },
});

apiClient.interceptors.request.use((config) => {
  if (WebApp?.initData) {
    config.headers["X-Telegram-Init-Data"] = WebApp.initData;
  }
  return config;
});