from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger

from models.screen_analyser import ScreenAnalyzer

app = FastAPI(
    title="Screen Analyzer API",
    version="1.0.0",
)

analyzer = ScreenAnalyzer(gpu=True)


class ScreenAnalyzeRequest(BaseModel):
    screenshot_base64: str
    metadata: Dict[str, Any]


class ScreenAnalyzeResponse(BaseModel):
    app_name: str
    content_type: str
    text_blocks: list
    detected_issues: list


@app.post("/analyze", response_model=ScreenAnalyzeResponse)
async def analyze_screen(payload: ScreenAnalyzeRequest):
    try:
        result = await analyzer.analyze(
            screenshot_base64=payload.screenshot_base64,
            metadata=payload.metadata,
        )
        return result
    except Exception as e:
        logger.exception("Unhandled error during screen analysis")
        raise HTTPException(status_code=500, detail="Internal Server Error")
