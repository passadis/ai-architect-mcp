from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="ArchitectAI Backend")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving (for diagrams/images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# API routes with /api prefix to match frontend expectations
app.include_router(api_router, prefix="/api")

# Health check at root
@app.get("/")
async def root():
    return {"message": "ArchitectAI Backend is running", "status": "healthy"}