from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime

from models.screen_analyser import capture_and_analyze
from models.ollama_engine import get_suggestion

# Initialize FastAPI app
app = FastAPI(title="NEXUS OCR API", version="1.0.0")

# CORS for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response model
class AnalysisResponse(BaseModel):
    metadata: dict
    suggestion: dict
    timestamp: str

# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "NEXUS OCR Backend",
        "message": "Ready to analyze screens"
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_screen():
    """
    Main endpoint: Capture screen → OCR → Extract metadata → Get AI suggestion
    This is called by Electron every 10 seconds
    """
    try:
        # Capture screen and extract metadata
        metadata = capture_and_analyze()
        
        # Get AI suggestion based on metadata
        suggestion = get_suggestion(metadata)
        
        return {
            "metadata": metadata,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Check if all systems operational"""
    return {
        "ocr": "ready",
        "ollama": "ready",
        "timestamp": datetime.now().isoformat()
    }

# Run server
if __name__ == "__main__":
    print("🚀 Starting NEXUS OCR Backend...")
    print("📍 Server: http://127.0.0.1:8000")
    print("📖 API Docs: http://127.0.0.1:8000/docs")
    print("🔍 Test: http://127.0.0.1:8000/")
    print("\n✅ Ready to receive requests from Electron app\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )