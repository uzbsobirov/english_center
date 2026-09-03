#!/bin/bash
# =========================================================
# ALPHA LC - 1-Click Production Deployment Script
# =========================================================

set -e

echo "🚀 [1/5] Yangilanishlar tekshirilmoqda..."
git pull origin main || true

echo "📦 [2/5] Docker konteynerlari yig'ilmoqda..."
docker-compose down
docker-compose build --no-cache

echo "🗄 [3/5] Ma'lumotlar bazasi ishga tushirilmoqda..."
docker-compose up -d postgres
sleep 3

echo "⚙️ [4/5] Bazani initsializatsiya qilish (Init DB)..."
docker-compose run --rm backend python init_db.py || true

echo "✨ [5/5] Barcha xizmatlar (Bot, Backend, Frontend, Nginx) ishga tushirilmoqda..."
docker-compose up -d

echo ""
echo "========================================================="
echo "🎉 ALPHA LC Muvaffaqiyatli Ishga Tushirildi!"
echo "📊 Nginx Port: 80"
echo "🤖 Telegram Bot: Ishlamoqda"
echo "🌐 WebApp: https://your-domain.com"
echo "========================================================="
docker-compose ps
