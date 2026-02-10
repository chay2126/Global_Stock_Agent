"""
FastAPI Backend for Global Stock Analyzer
Phase 1: Basic API Setup
Phase 2: Serve Frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="Global Stock Analyzer API",
    description="Analyze stocks from any exchange worldwide - Get BUY/SELL/HOLD recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - allows frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Import API routes
from backend.api import routes

# Include API routes
app.include_router(routes.router, prefix="/api", tags=["Stock Analysis"])


# Root endpoint - serves the frontend HTML
@app.get("/")
async def root():
    """
    Root endpoint - serves the frontend application.
    """
    return FileResponse("frontend/index.html")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy", "message": "API is running!"}


