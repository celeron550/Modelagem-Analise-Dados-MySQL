from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analytics, auth, avaliacoes, catalogo

app = FastAPI(title="MusicRate API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Infra"])
def health_check():
    return {"status": "ok", "milestone": "marco-0"}

app.include_router(auth.router)
app.include_router(catalogo.router)
app.include_router(avaliacoes.router)
app.include_router(analytics.router)