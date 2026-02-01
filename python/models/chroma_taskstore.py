"""
NEXUS ChromaDB Task Store
Dedicated storage layer for tasks, subtasks, and completion patterns
Separates storage logic from business logic in task_manager.py
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime
import chromadb
from chromadb.config import Settings


class ChromaTaskStore:
    """
    ChromaDB storage interface for NEXUS tasks
    Handles persistence, retrieval, and pattern storage
    """
    
    def __init__(self, chroma_path: str = "./chroma_db"):
        """
        Initialize ChromaDB collections
        
        Args:
            chroma_path: Path to ChromaDB persistence directory
        """
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Task storage collection
        self.tasks = self.client.get_or_create_collection(
            name="nexus_tasks",
            metadata={"description": "Main task and subtask storage"}
        )
        
        # Pattern learning collection
        self.patterns = self.client.get_or_create_collection(
            name="nexus_patterns",
            metadata={"description": "User completion patterns for ML"}
        )
        
        # Activity metadata collection (from screen analyzer)
        self.activities = self.client.get_or_create_collection(
            name="nexus_activities",
            metadata={"description": "Screen activity context for RAG"}
        )
    
    # ========================================================================
    # TASK CRUD
    # ========================================================================
    
    def save_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Save or update a task
        
        Args:
            task_id: Unique task identifier
            task_data: Full task dictionary (from Task.to_dict())
        """
        # Create searchable document
        document = self._task_to_document(task_data)
        
        # Upsert (add or update)
        self.tasks.upsert(
            documents=[document],
            metadatas=[task_data],
            ids=[task_id]
        )
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        result = self.tasks.get(ids=[task_id])
        
        if not result['metadatas']:
            return None
        
        return result['metadatas'][0]
    
    def get_all_tasks(
        self,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks with optional filtering
        
        Args:
            where: ChromaDB where clause (e.g., {"status": "pending"})
            limit: Max results to return
        """
        result = self.tasks.get(where=where, limit=limit)
        return result['metadatas']
    
    def delete_task(self, task_id: str) -> bool:
        """Delete task by ID"""
        try:
            self.tasks.delete(ids=[task_id])
            return True
        except Exception:
            return False
    
    def query_tasks(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for tasks
        
        Args:
            query_text: Natural language query
            n_results: Number of results
            where: Optional metadata filter
        """
        result = self.tasks.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        
        return result['metadatas'][0] if result['metadatas'] else []
    
    # ========================================================================
    # PATTERN STORAGE
    # ========================================================================
    
    def save_pattern(
        self,
        pattern_id: str,
        task_id: str,
        pattern_type: str,
        data: Dict[str, Any]
    ):
        """
        Store completion pattern for learning
        
        Args:
            pattern_id: Unique pattern identifier
            task_id: Related task ID
            pattern_type: Type (e.g., "completion", "breakdown", "stuck")
            data: Pattern data dictionary
        """
        metadata = {
            "task_id": task_id,
            "pattern_type": pattern_type,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        document = json.dumps(data)
        
        self.patterns.add(
            documents=[document],
            metadatas=[metadata],
            ids=[pattern_id]
        )
    
    def get_patterns(
        self,
        task_id: Optional[str] = None,
        pattern_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve patterns with optional filtering
        
        Args:
            task_id: Filter by specific task
            pattern_type: Filter by pattern type
            limit: Max results
        """
        where = {}
        if task_id:
            where["task_id"] = task_id
        if pattern_type:
            where["pattern_type"] = pattern_type
        
        result = self.patterns.get(
            where=where if where else None,
            limit=limit
        )
        
        return result['metadatas']
    
    # ========================================================================
    # ACTIVITY CONTEXT (for RAG integration)
    # ========================================================================
    
    def save_activity(
        self,
        activity_id: str,
        metadata: Dict[str, Any],
        document: str
    ):
        """
        Save screen activity context
        
        Args:
            activity_id: Unique activity ID (timestamp-based)
            metadata: Activity metadata from screen_analyzer
            document: Searchable text representation
        """
        self.activities.add(
            documents=[document],
            metadatas=[metadata],
            ids=[activity_id]
        )
    
    def query_activities(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query recent activities for context
        
        Args:
            query_text: Search query
            n_results: Number of results
            where: Metadata filter
        """
        result = self.activities.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        
        return result['metadatas'][0] if result['metadatas'] else []
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _task_to_document(self, task_data: Dict[str, Any]) -> str:
        """Convert task dict to searchable document"""
        subtask_titles = [
            st['title'] for st in task_data.get('subtasks', [])
        ]
        
        doc = f"""Task: {task_data['title']}
Description: {task_data['description']}
Priority: {task_data['priority']}
Status: {task_data['status']}
Context: {task_data.get('context', 'None')}
Tags: {', '.join(task_data.get('tags', []))}
Subtasks: {', '.join(subtask_titles)}"""
        
        return doc
    
    def get_stats(self) -> Dict[str, int]:
        """Get collection statistics"""
        return {
            "total_tasks": self.tasks.count(),
            "total_patterns": self.patterns.count(),
            "total_activities": self.activities.count()
        }
    
    def clear_all(self):
        """Clear all collections (use with caution!)"""
        self.client.delete_collection("nexus_tasks")
        self.client.delete_collection("nexus_patterns")
        self.client.delete_collection("nexus_activities")
        
        # Recreate
        self.__init__()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize store
    store = ChromaTaskStore()
    
    # Example task data
    task_data = {
        "id": "task-123",
        "title": "Build authentication system",
        "description": "User login with JWT tokens",
        "priority": "high",
        "status": "in_progress",
        "context": "Critical for launch",
        "tags": ["backend", "security"],
        "subtasks": [
            {"title": "Setup JWT library", "status": "completed"},
            {"title": "Create login endpoint", "status": "in_progress"}
        ],
        "created_at": datetime.now().isoformat()
    }
    
    # Save task
    store.save_task("task-123", task_data)
    print("✅ Task saved")
    
    # Retrieve task
    retrieved = store.get_task("task-123")
    print(f"📦 Retrieved: {retrieved['title']}")
    
    # Semantic search
    results = store.query_tasks("authentication and security")
    print(f"🔍 Found {len(results)} matching tasks")
    
    # Save pattern
    store.save_pattern(
        pattern_id="pattern-456",
        task_id="task-123",
        pattern_type="completion",
        data={"time_spent": 25, "cognitive_state": "focused"}
    )
    print("📊 Pattern saved")
    
    # Stats
    print(f"\n📈 Stats: {store.get_stats()}")