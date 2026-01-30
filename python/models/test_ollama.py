import pytest
from ollama_engine import NexusOllamaEngine, get_suggestion
from datetime import datetime

def test_engine_initialization():
    """Test Ollama engine initializes correctly"""
    engine = NexusOllamaEngine()
    assert engine.llm is not None
    assert engine.vectorstore is not None
    print("✓ Engine initialized successfully")

def test_add_memory():
    """Test adding metadata to vector store"""
    engine = NexusOllamaEngine()
    
    metadata = {
        "app_name": "VSCode",
        "ocr_text": "def hello_world(): print('test')",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test_session_1"
    }
    
    engine.add_memory(metadata)
    print("✓ Memory added successfully")

def test_get_suggestion_no_error():
    """Test suggestion generation - no errors"""
    metadata = {
        "app_name": "Chrome",
        "ocr_text": "Reading documentation on React hooks",
        "timestamp": datetime.now().isoformat(),
        "idle_time": 30,
        "errors": []
    }
    
    result = get_suggestion(metadata)
    
    assert "message" in result
    assert "show_notification" in result
    assert result["show_notification"] == False  # No stuck/error
    print(f"✓ Suggestion (no alert): {result['message']}")

def test_get_suggestion_stuck_detected():
    """Test suggestion when user is stuck"""
    metadata = {
        "app_name": "VSCode",
        "ocr_text": "SyntaxError: invalid syntax",
        "timestamp": datetime.now().isoformat(),
        "idle_time": 150,  # 2.5 min idle
        "errors": ["SyntaxError"]
    }
    
    result = get_suggestion(metadata)
    
    assert result["show_notification"] == True  # Should notify
    print(f"✓ Suggestion (stuck alert): {result['message']}")

def test_session_summary():
    """Test session summarization"""
    engine = NexusOllamaEngine()
    
    # Add multiple memories
    for i in range(3):
        metadata = {
            "app_name": "VSCode",
            "ocr_text": f"Writing code iteration {i}",
            "timestamp": datetime.now().isoformat(),
            "session_id": "test_session_summary"
        }
        engine.add_memory(metadata)
    
    summary = engine.summarize_session("test_session_summary")
    assert len(summary) > 0
    print(f"✓ Session summary: {summary}")

if __name__ == "__main__":
    print("Running NEXUS Ollama Engine Tests...\n")
    
    test_engine_initialization()
    test_add_memory()
    test_get_suggestion_no_error()
    test_get_suggestion_stuck_detected()
    test_session_summary()
    
    print("\n✅ All tests passed!")