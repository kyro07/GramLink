# main.py
# This is the main entry point of your FastAPI application

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all route handlers
from routers import missed_call, whatsapp, driver, eta, register, buses, feedback

# ─────────────────────────────────────────────
# CREATE FASTAPI APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="GramLink API",
    description="Voice-First Rural Bus Tracking System for Tamil Nadu",
    version="1.0.0",
    docs_url="/docs",       # API documentation at /docs
    redoc_url="/redoc"      # Alternative docs at /redoc
)

# ─────────────────────────────────────────────
# CORS MIDDLEWARE
# Allows requests from Flutter app, web browser, etc.
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# INCLUDE ALL ROUTERS
# Each router handles a group of related endpoints
# ─────────────────────────────────────────────
app.include_router(missed_call.router, tags=["Infobip Webhooks"])
app.include_router(whatsapp.router, tags=["Infobip Webhooks"])
app.include_router(driver.router, tags=["Driver App"])
app.include_router(eta.router, tags=["ETA"])
app.include_router(register.router, tags=["Users"])
app.include_router(buses.router, tags=["Buses"])
app.include_router(feedback.router, tags=["ML Feedback"])

# ─────────────────────────────────────────────
# ROOT ENDPOINT — Health Check
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "🚌 GramLink API is running", 
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "gramlink"}

# ─────────────────────────────────────────────
# GLOBAL ERROR HANDLER
# ─────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": str(request.url)}
    )

# ─────────────────────────────────────────────
# START SERVER
# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True       # Auto-reload on code changes
    )

