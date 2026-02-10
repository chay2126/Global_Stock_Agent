from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="Global Stock Analyzer API",
    description="Analyze stocks from any exchange worldwide - Get BUY/SELL/HOLD recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# CORS configuration - allows frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Import API routes
from backend.api import routes

# Include API routes
app.include_router(routes.router, prefix="/api", tags=["Stock Analysis"])

# Root endpoint - serves the frontend HTML
@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running!"}
