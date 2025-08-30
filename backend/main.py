from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api.agent_api import router as agent_router

app = FastAPI(
    title="🧠 Cognitive Commerce API",
    version="1.0.0",
    docs_url="/docs", redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(agent_router)  # prefix YOK

app.mount("/static", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health():
    return {"message": "✅ Cognitive Commerce Platform is up and running."}
