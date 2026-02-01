import easyocr
import pyautogui
import psutil
from PIL import Image
import numpy as np
from datetime import datetime

import platform
import io

class ScreenAnalyzer:
    def __init__(self):
        # Initialize EasyOCR with English language
        self.reader = easyocr.Reader(['en'], gpu=True)  # Set gpu=True if you have CUDA
        self.last_activity_time = datetime.now()
        self.previous_text = ""
        
    def capture_screen(self) -> Image.Image:
        """Capture current screen"""
        screenshot = pyautogui.screenshot()
        return screenshot
    
    def extract_text_ocr(self, image: Image.Image) -> str:
        """Extract text from image using EasyOCR"""
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Perform OCR
        results = self.reader.readtext(img_array, detail=0)  # detail=0 returns only text
        
        # Join all text with spaces
        extracted_text = " ".join(results)
        return extracted_text
    
    def detect_active_app(self) -> dict:
        """Detect currently active application"""
        try:
            if platform.system() == "Windows":
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                app_name = buff.value
                return {"app_name": app_name, "window_title": app_name}
            
            elif platform.system() == "Darwin":  # macOS
                from AppKit import NSWorkspace
                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                return {
                    "app_name": active_app['NSApplicationName'],
                    "window_title": active_app.get('NSApplicationName', '')
                }
            
            elif platform.system() == "Linux":
                # Linux requires wmctrl or xdotool
                import subprocess
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], 
                                      capture_output=True, text=True)
                return {"app_name": "Unknown", "window_title": result.stdout.strip()}
                
        except Exception as e:
            return {"app_name": "Unknown", "window_title": f"Error: {str(e)}"}
    
    def detect_errors(self, text: str) -> list:
        """Detect common error patterns in screen text"""
        error_keywords = [
            "error", "exception", "failed", "traceback", 
            "syntaxerror", "typeerror", "nameerror", "undefined",
            "cannot", "unable", "forbidden", "denied"
        ]
        
        detected_errors = []
        text_lower = text.lower()
        
        for keyword in error_keywords:
            if keyword in text_lower:
                detected_errors.append(keyword.capitalize())
        
        return list(set(detected_errors))  # Remove duplicates
    
    def detect_stuck(self, current_text: str) -> int:
        """Detect if user is stuck (no text change)"""
        # Compare with previous text
        if current_text == self.previous_text:
            idle_time = (datetime.now() - self.last_activity_time).total_seconds()
        else:
            self.last_activity_time = datetime.now()
            self.previous_text = current_text
            idle_time = 0
        
        return int(idle_time)
    
    def get_system_stats(self) -> dict:
        """Get CPU and memory usage"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent
        }
    
    def analyze(self) -> dict:
        """Main analysis pipeline - captures screen and extracts all metadata"""
        
        # Step 1: Capture screen
        screenshot = self.capture_screen()
        
        # Step 2: OCR text extraction
        ocr_text = self.extract_text_ocr(screenshot)
        
        # Step 3: Detect active app
        app_info = self.detect_active_app()
        
        # Step 4: Detect errors
        errors = self.detect_errors(ocr_text)
        
        # Step 5: Detect stuck/idle
        idle_time = self.detect_stuck(ocr_text)
        
        # Step 6: System stats
        sys_stats = self.get_system_stats()
        
        # Build metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "app_name": app_info["app_name"],
            "window_title": app_info["window_title"],
            "ocr_text": ocr_text[:500],  # Limit to 500 chars
            "errors": errors,
            "idle_time": idle_time,
            "cpu_percent": sys_stats["cpu_percent"],
            "memory_percent": sys_stats["memory_percent"],
            "session_id": "default"  # Will be set by main app
        }
        
        # Screenshot is NOT saved - privacy first!
        return metadata


# Singleton instance
analyzer = ScreenAnalyzer()

def capture_and_analyze() -> dict:
    """Main interface for FastAPI"""
    return analyzer.analyze()