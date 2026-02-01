# Create test_full.py
from screen_analyser import capture_and_analyze
from ollama_engine import get_suggestion

metadata = capture_and_analyze()
suggestion = get_suggestion(metadata)

print(f"\n🖥️ Detected: {metadata['app_name']}")
print(f"📝 Text: {metadata['ocr_text'][:100]}")
print(f"🤖 NEXUS: {suggestion['message']}")
print(f"🔔 Notify: {suggestion['show_notification']}")