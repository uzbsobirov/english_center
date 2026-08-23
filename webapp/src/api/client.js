import axios from "axios";
import WebApp from "../lib/telegram";

const BASE_URL = "https://dts-urls-brush-vault.trycloudflare.com";

export const apiClient = axios.create({
  baseURL: BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  config.headers["X-Telegram-Init-Data"] = WebApp.initData || "";
  return config;
});