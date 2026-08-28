"""
FastAPI backend - Web App uchun API.
...
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.deps import get_current_telegram_user
from backend.api.routes import tests, courses, teacher, admin, student

app = FastAPI(title="English Center API", version="2.6")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.6"}


@app.get("/api/me")
async def me(user: dict = Depends(get_current_telegram_user)):
    return {"telegram_user": user}


# Routers
app.include_router(tests.router)
app.include_router(courses.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(student.router)


