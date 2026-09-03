FROM python:3.12-slim

# Tizim paketlarini o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bog'liqliklarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini ko'chirish
COPY . .

# Chiqish porti (FastAPI)
EXPOSE 8000

# Standart ishga tushirish buyrug'i
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
