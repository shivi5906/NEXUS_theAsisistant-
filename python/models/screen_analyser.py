from __future__ import annotations

import base64
import io
import asyncio
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from loguru import logger
import easyocr


class ScreenAnalyzer:
    """
    Analyzes a screenshot to extract text, detect application type,
    content type, and possible issues (errors/exceptions).
    """

    ERROR_KEYWORDS = ("error", "exception", "failed", "traceback")

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        gpu: bool = True,
    ) -> None:
        self.languages = languages or ["en"]
        self.gpu = gpu

        try:
            self.reader = easyocr.Reader(
                self.languages,
                gpu=self.gpu,
                verbose=False,
            )
            logger.info(f"EasyOCR initialized (GPU={self.gpu})")
        except Exception as e:
            logger.exception("Failed to initialize EasyOCR, falling back to CPU")
            self.reader = easyocr.Reader(self.languages, gpu=False, verbose=False)

    # ----------------------------- Public API -----------------------------

    async def analyze(
        self,
        screenshot_base64: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main async analysis method.
        """
        try:
            image = self._decode_image(screenshot_base64)
        except Exception as e:
            logger.exception("Image decoding failed")
            return self._error_response("Invalid image data")

        try:
            preprocessed = await asyncio.to_thread(self._preprocess_image, image)
            ocr_results = await asyncio.to_thread(self._run_ocr, preprocessed)
        except Exception as e:
            logger.exception("OCR processing failed")
            return self._error_response("OCR failed")

        text_blocks = self._format_text_blocks(ocr_results)
        full_text = " ".join(tb["text"] for tb in text_blocks).lower()

        app_name = self._detect_application(metadata)
        content_type = self._detect_content_type(
            full_text=full_text,
            window_title=metadata.get("window_title", ""),
        )
        detected_issues = self._detect_issues(text_blocks)

        return {
            "app_name": app_name,
            "content_type": content_type,
            "text_blocks": text_blocks,
            "detected_issues": detected_issues,
        }

    # ----------------------------- OCR & Image -----------------------------

    def _decode_image(self, screenshot_base64: str) -> np.ndarray:
        image_bytes = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Light preprocessing for speed + OCR accuracy.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return thresh

    def _run_ocr(self, image: np.ndarray) -> List[Any]:
        return self.reader.readtext(
            image,
            detail=1,
            paragraph=False,
        )

    # ----------------------------- Detection Logic -----------------------------

    def _detect_application(self, metadata: Dict[str, Any]) -> str:
        title = metadata.get("window_title", "").lower()

        if "chrome" in title or "edge" in title or "firefox" in title:
            return "Browser"
        if "vscode" in title or "visual studio" in title:
            return "VS Code"
        if "terminal" in title or "powershell" in title:
            return "Terminal"
        if "slack" in title:
            return "Slack"
        if "outlook" in title or "gmail" in title:
            return "Email Client"
        if "word" in title or "docs" in title:
            return "Document Editor"

        return "Unknown"

    def _detect_content_type(self, full_text: str, window_title: str) -> str:
        title = window_title.lower()

        if any(k in full_text for k in ["def ", "{", "};", "#include", "import "]):
            return "code"
        if any(k in full_text for k in ["from:", "to:", "subject:"]):
            return "email"
        if "http" in full_text or "www" in full_text or "browser" in title:
            return "browser"
        if len(full_text.split()) > 50:
            return "document"

        return "unknown"

    def _detect_issues(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        issues = []

        for block in text_blocks:
            text_lower = block["text"].lower()
            if any(keyword in text_lower for keyword in self.ERROR_KEYWORDS):
                issues.append(
                    {
                        "text": block["text"],
                        "bbox": block["bbox"],
                        "severity": "error",
                    }
                )

        return issues

    # ----------------------------- Helpers -----------------------------

    def _format_text_blocks(self, ocr_results: List[Any]) -> List[Dict[str, Any]]:
        blocks = []

        for bbox, text, confidence in ocr_results:
            blocks.append(
                {
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": self._normalize_bbox(bbox),
                }
            )

        return blocks

    def _normalize_bbox(self, bbox: List[List[float]]) -> List[Tuple[int, int]]:
        return [(int(x), int(y)) for x, y in bbox]

    def _error_response(self, message: str) -> Dict[str, Any]:
        return {
            "app_name": "Unknown",
            "content_type": "unknown",
            "text_blocks": [],
            "detected_issues": [{"message": message}],
        }
