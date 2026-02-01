"""
NEXUS Task Manager
Handles task breakdown, storage, and intelligent scheduling for ADHD users
Integrates with Ollama for intelligent decomposition and ChromaDB for storage
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import uuid

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import chromadb
from chromadb.config import Settings


# ============================================================================
# DATA MODELS
# ============================================================================

class TaskStatus(str, Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STUCK = "stuck"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CognitiveState(str, Enum):
    """User's current cognitive/emotional state for smart scheduling"""
    FOCUSED = "focused"  # High concentration, good for complex tasks
    ENERGIZED = "energized"  # High energy, good for active tasks
    CALM = "calm"  # Steady state, good for routine tasks
    TIRED = "tired"  # Low energy, good for simple tasks
    STRESSED = "stressed"  # Anxious, need easy wins
    UNKNOWN = "unknown"  # No emotion detection data


@dataclass
class Subtask:
    """Individual subtask within a parent task"""
    id: str
    parent_task_id: str
    title: str
    description: str
    estimated_minutes: int
    status: TaskStatus = TaskStatus.PENDING
    order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_spent_minutes: int = 0
    stuck_count: int = 0
    requires_state: Optional[CognitiveState] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        if self.requires_state:
            data['requires_state'] = self.requires_state.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subtask':
        """Create from dictionary"""
        data['status'] = TaskStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['started_at'] = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        if data.get('requires_state'):
            data['requires_state'] = CognitiveState(data['requires_state'])
        return cls(**data)


@dataclass
class Task:
    """Main task containing multiple subtasks"""
    id: str
    title: str
    description: str
    subtasks: List[Subtask]
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'subtasks': [st.to_dict() for st in self.subtasks],
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'tags': self.tags,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary"""
        data['subtasks'] = [Subtask.from_dict(st) for st in data['subtasks']]
        data['priority'] = TaskPriority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['deadline'] = datetime.fromisoformat(data['deadline']) if data.get('deadline') else None
        return cls(**data)
    
    def get_progress(self) -> float:
        """Calculate completion percentage"""
        if not self.subtasks:
            return 0.0
        completed = sum(1 for st in self.subtasks if st.status == TaskStatus.COMPLETED)
        return (completed / len(self.subtasks)) * 100
    
    def get_next_subtask(self) -> Optional[Subtask]:
        """Get next pending subtask in order"""
        pending = [st for st in self.subtasks if st.status == TaskStatus.PENDING]
        return min(pending, key=lambda x: x.order) if pending else None


# Pydantic models for Ollama JSON output parsing
class SubtaskSchema(BaseModel):
    """Schema for subtask generation"""
    title: str = Field(description="Short, action-oriented subtask title (max 60 chars)")
    description: str = Field(description="Clear description of what needs to be done")
    estimated_minutes: int = Field(description="Realistic time estimate (15-30 minutes)")
    requires_state: Optional[str] = Field(description="Best cognitive state: focused, energized, calm, tired, stressed")


class TaskBreakdownSchema(BaseModel):
    """Schema for complete task breakdown"""
    subtasks: List[SubtaskSchema] = Field(description="List of 5-10 ADHD-friendly subtasks")
    reasoning: str = Field(description="Why this breakdown works for ADHD")


# ============================================================================
# TASK MANAGER CLASS
# ============================================================================

class TaskManager:
    """
    Manages task breakdown, storage, and intelligent scheduling
    Optimized for ADHD users with progressive disclosure and adaptive scheduling
    """
    
    def __init__(
        self,
        ollama_model: str = "llama3.2:3b",
        chroma_path: str = "./chroma_db",
        ollama_base_url: str = "http://localhost:11434"
    ):
        """
        Initialize TaskManager
        
        Args:
            ollama_model: Ollama model name for task breakdown
            chroma_path: Path to ChromaDB storage
            ollama_base_url: Ollama server URL
        """
        # Initialize Ollama LLM
        self.llm = ChatOllama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.7,
            format="json"
        )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create separate collections
        self.tasks_collection = self.chroma_client.get_or_create_collection(
            name="nexus_tasks",
            metadata={"description": "Task and subtask storage"}
        )
        
        self.patterns_collection = self.chroma_client.get_or_create_collection(
            name="nexus_task_patterns",
            metadata={"description": "User task completion patterns for smart scheduling"}
        )
        
        # Setup breakdown prompt
        self._setup_breakdown_prompt()
    
    def _setup_breakdown_prompt(self):
        """Setup the ADHD-optimized task breakdown prompt"""
        self.breakdown_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an ADHD task breakdown specialist. Your job is to decompose large, overwhelming tasks into small, manageable subtasks optimized for ADHD brains.

ADHD-Friendly Task Breakdown Principles:
1. **Small Wins**: Each subtask should be 15-30 minutes max (ADHD optimal focus time)
2. **Clear Actions**: Start with action verbs (Create, Write, Research, Review, Send)
3. **No Ambiguity**: Each subtask should have ONE clear outcome
4. **Progressive Disclosure**: User sees only current task, not the whole mountain
5. **Quick Dopamine**: Early tasks should be easier to build momentum
6. **Variety**: Mix different types of tasks to prevent boredom
7. **State-Aware**: Match tasks to cognitive states (focused vs tired vs stressed)

Cognitive State Matching:
- **focused**: Complex problem-solving, writing, coding, analysis
- **energized**: Active tasks, organizing, outreach, physical tasks
- **calm**: Routine tasks, documentation, data entry, reviews
- **tired**: Simple tasks, organizing files, checking emails, cleanup
- **stressed**: Easy wins, familiar tasks, low-stakes activities

Output Format: JSON with this structure:
{{
  "subtasks": [
    {{
      "title": "Action-oriented title (max 60 chars)",
      "description": "What exactly needs to be done",
      "estimated_minutes": 20,
      "requires_state": "focused"
    }}
  ],
  "reasoning": "Why this breakdown works for ADHD"
}}

Generate 5-10 subtasks. Put easier tasks first for momentum."""),
            ("user", """Break down this task for someone with ADHD:

Task: {task_title}
Description: {task_description}
Priority: {priority}
{context}

Remember: Small, clear, actionable steps. Each subtask = 15-30 minutes max.""")
        ])
        
        # Create the breakdown chain
        self.breakdown_chain = (
            self.breakdown_prompt 
            | self.llm 
            | JsonOutputParser(pydantic_object=TaskBreakdownSchema)
        )
    
    # ========================================================================
    # TASK BREAKDOWN
    # ========================================================================
    
    async def breakdown_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        deadline: Optional[datetime] = None
    ) -> Task:
        """
        Break down a large task into ADHD-friendly subtasks
        
        Args:
            title: Main task title
            description: Detailed description of the task
            priority: Task priority level
            context: Why this task matters (motivational context)
            tags: Optional tags for categorization
            deadline: Optional deadline
            
        Returns:
            Task object with generated subtasks
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Prepare context string
        context_str = f"Context/Motivation: {context}" if context else "No additional context provided"
        
        # Call Ollama to break down the task
        breakdown_result = await self.breakdown_chain.ainvoke({
            "task_title": title,
            "task_description": description,
            "priority": priority.value,
            "context": context_str
        })
        
        # Convert to Subtask objects
        subtasks = []
        for idx, st_data in enumerate(breakdown_result['subtasks']):
            # Map cognitive state
            state = None
            if st_data.get('requires_state'):
                try:
                    state = CognitiveState(st_data['requires_state'].lower())
                except ValueError:
                    state = CognitiveState.UNKNOWN
            
            subtask = Subtask(
                id=str(uuid.uuid4()),
                parent_task_id=task_id,
                title=st_data['title'],
                description=st_data['description'],
                estimated_minutes=min(st_data['estimated_minutes'], 30),
                order=idx,
                requires_state=state
            )
            subtasks.append(subtask)
        
        # Create main task
        task = Task(
            id=task_id,
            title=title,
            description=description,
            subtasks=subtasks,
            priority=priority,
            context=context,
            tags=tags or [],
            deadline=deadline
        )
        
        # Store in ChromaDB
        self._store_task(task)
        
        # Store breakdown reasoning
        self._store_pattern(
            task_id=task_id,
            pattern_type="breakdown",
            data={"reasoning": breakdown_result.get('reasoning', '')}
        )
        
        return task
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def _store_task(self, task: Task):
        """Store task in ChromaDB with flattened metadata"""
        task_dict = task.to_dict()
        
        # Create searchable document
        document = f"""Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}
Context: {task.context or 'None'}
Subtasks: {', '.join([st.title for st in task.subtasks])}"""
        
        # FLATTEN metadata for ChromaDB (no nested objects)
        flat_metadata = {
            'id': task_dict['id'],
            'title': task_dict['title'],
            'description': task_dict['description'],
            'priority': task_dict['priority'],
            'status': task_dict['status'],
            'created_at': task_dict['created_at'],
            'deadline': task_dict.get('deadline') or '',
            'context': task_dict.get('context') or '',
            'tags': ','.join(task_dict.get('tags', [])),
            'subtasks_json': json.dumps(task_dict['subtasks'])
        }
        
        self.tasks_collection.add(
            documents=[document],
            metadatas=[flat_metadata],
            ids=[task.id]
        )
    
    def _update_task(self, task: Task):
        """Update existing task in ChromaDB"""
        self.tasks_collection.delete(ids=[task.id])
        self._store_task(task)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID"""
        result = self.tasks_collection.get(ids=[task_id])
        
        if not result['metadatas']:
            return None
        
        # Reconstruct full task dict from flattened metadata
        meta = result['metadatas'][0]
        task_dict = {
            'id': meta['id'],
            'title': meta['title'],
            'description': meta['description'],
            'priority': meta['priority'],
            'status': meta['status'],
            'created_at': meta['created_at'],
            'deadline': meta.get('deadline') if meta.get('deadline') else None,
            'context': meta.get('context', ''),
            'tags': meta.get('tags', '').split(',') if meta.get('tags') else [],
            'subtasks': json.loads(meta['subtasks_json'])
        }
        
        return Task.from_dict(task_dict)
    
    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get all tasks, optionally filtered by status"""
        result = self.tasks_collection.get()
        
        tasks = []
        for meta in result['metadatas']:
            task_dict = {
                'id': meta['id'],
                'title': meta['title'],
                'description': meta['description'],
                'priority': meta['priority'],
                'status': meta['status'],
                'created_at': meta['created_at'],
                'deadline': meta.get('deadline') if meta.get('deadline') else None,
                'context': meta.get('context', ''),
                'tags': meta.get('tags', '').split(',') if meta.get('tags') else [],
                'subtasks': json.loads(meta['subtasks_json'])
            }
            tasks.append(Task.from_dict(task_dict))
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)
    
    def update_subtask_status(
        self,
        task_id: str,
        subtask_id: str,
        status: TaskStatus,
        time_spent: Optional[int] = None
    ) -> Optional[Task]:
        """
        Update subtask status and time tracking
        
        Args:
            task_id: Parent task ID
            subtask_id: Subtask ID
            status: New status
            time_spent: Minutes spent on this subtask
            
        Returns:
            Updated Task object
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Find and update subtask
        for subtask in task.subtasks:
            if subtask.id == subtask_id:
                old_status = subtask.status
                subtask.status = status
                
                # Track time
                if time_spent:
                    subtask.time_spent_minutes += time_spent
                
                # Update timestamps
                if status == TaskStatus.IN_PROGRESS and not subtask.started_at:
                    subtask.started_at = datetime.now()
                elif status == TaskStatus.COMPLETED:
                    subtask.completed_at = datetime.now()
                elif status == TaskStatus.STUCK:
                    subtask.stuck_count += 1
                
                # Store pattern for learning
                self._store_pattern(
                    task_id=task_id,
                    pattern_type="completion",
                    data={
                        "subtask_id": subtask_id,
                        "old_status": old_status.value,
                        "new_status": status.value,
                        "time_spent": time_spent,
                        "stuck_count": subtask.stuck_count
                    }
                )
                
                break
        
        # Update parent task status
        all_completed = all(st.status == TaskStatus.COMPLETED for st in task.subtasks)
        if all_completed:
            task.status = TaskStatus.COMPLETED
        elif any(st.status == TaskStatus.IN_PROGRESS for st in task.subtasks):
            task.status = TaskStatus.IN_PROGRESS
        
        # Save updated task
        self._update_task(task)
        
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            self.tasks_collection.delete(ids=[task_id])
            return True
        except Exception:
            return False
    
    # ========================================================================
    # SMART SCHEDULING
    # ========================================================================
    
    def get_next_best_subtask(
        self,
        current_state: CognitiveState = CognitiveState.UNKNOWN,
        exclude_task_ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next best subtask based on cognitive state and patterns
        
        Args:
            current_state: User's current cognitive/emotional state
            exclude_task_ids: Task IDs to exclude from selection
            
        Returns:
            Dict with task and subtask info, or None
        """
        exclude_task_ids = exclude_task_ids or []
        
        # Get all active tasks
        active_tasks = [
            t for t in self.get_all_tasks() 
            if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
            and t.id not in exclude_task_ids
        ]
        
        if not active_tasks:
            return None
        
        # Collect all pending subtasks with scoring
        candidates = []
        for task in active_tasks:
            for subtask in task.subtasks:
                if subtask.status == TaskStatus.PENDING:
                    score = self._score_subtask(subtask, task, current_state)
                    candidates.append({
                        'task': task,
                        'subtask': subtask,
                        'score': score
                    })
        
        if not candidates:
            return None
        
        # Return highest scoring subtask
        best = max(candidates, key=lambda x: x['score'])
        
        return {
            'task_id': best['task'].id,
            'task_title': best['task'].title,
            'subtask_id': best['subtask'].id,
            'subtask_title': best['subtask'].title,
            'subtask_description': best['subtask'].description,
            'estimated_minutes': best['subtask'].estimated_minutes,
            'priority': best['task'].priority.value,
            'context': best['task'].context,
            'progress': best['task'].get_progress(),
            'score': best['score']
        }
    
    def _score_subtask(
        self,
        subtask: Subtask,
        task: Task,
        current_state: CognitiveState
    ) -> float:
        """
        Score a subtask for scheduling priority
        
        Scoring factors:
        - Cognitive state match (40%)
        - Task priority (25%)
        - Task order (20%)
        - Low stuck count (15%)
        """
        score = 0.0
        
        # Cognitive state match (40 points max)
        if current_state != CognitiveState.UNKNOWN:
            if subtask.requires_state == current_state:
                score += 40
            elif subtask.requires_state == CognitiveState.UNKNOWN:
                score += 20
            elif current_state == CognitiveState.TIRED and subtask.requires_state == CognitiveState.CALM:
                score += 30
            elif current_state == CognitiveState.STRESSED and subtask.requires_state in [CognitiveState.CALM, CognitiveState.TIRED]:
                score += 25
        else:
            score += 20
        
        # Task priority (25 points max)
        priority_scores = {
            TaskPriority.URGENT: 25,
            TaskPriority.HIGH: 20,
            TaskPriority.MEDIUM: 12,
            TaskPriority.LOW: 5
        }
        score += priority_scores.get(task.priority, 10)
        
        # Order bonus (20 points max)
        max_order = max(st.order for st in task.subtasks)
        if max_order > 0:
            order_score = 20 * (1 - (subtask.order / max_order))
            score += order_score
        else:
            score += 20
        
        # Stuck penalty (15 points max)
        stuck_penalty = min(subtask.stuck_count * 3, 15)
        score += (15 - stuck_penalty)
        
        return score
    
    # ========================================================================
    # FURTHER BREAKDOWN (for stuck situations)
    # ========================================================================
    
    async def breakdown_subtask(
        self,
        task_id: str,
        subtask_id: str
    ) -> Optional[Task]:
        """
        Break down a subtask that user is stuck on into even smaller pieces
        
        Args:
            task_id: Parent task ID
            subtask_id: Stuck subtask ID
            
        Returns:
            Updated task with new micro-subtasks inserted
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Find the stuck subtask
        stuck_subtask = None
        stuck_index = -1
        for idx, st in enumerate(task.subtasks):
            if st.id == subtask_id:
                stuck_subtask = st
                stuck_index = idx
                break
        
        if not stuck_subtask:
            return None
        
        # Call Ollama to break down further
        micro_breakdown = await self.breakdown_chain.ainvoke({
            "task_title": stuck_subtask.title,
            "task_description": stuck_subtask.description,
            "priority": task.priority.value,
            "context": "User got stuck on this subtask. Break it into 3-5 even smaller micro-tasks (10-15 min each)."
        })
        
        # Create micro-subtasks
        micro_subtasks = []
        for idx, st_data in enumerate(micro_breakdown['subtasks'][:5]):
            state = None
            if st_data.get('requires_state'):
                try:
                    state = CognitiveState(st_data['requires_state'].lower())
                except ValueError:
                    state = CognitiveState.UNKNOWN
            
            micro_subtask = Subtask(
                id=str(uuid.uuid4()),
                parent_task_id=task_id,
                title=f"↳ {st_data['title']}",
                description=st_data['description'],
                estimated_minutes=min(st_data['estimated_minutes'], 15),
                order=stuck_index + idx + 0.1,
                requires_state=state
            )
            micro_subtasks.append(micro_subtask)
        
        # Mark original subtask as skipped and insert micro-tasks
        stuck_subtask.status = TaskStatus.SKIPPED
        task.subtasks = (
            task.subtasks[:stuck_index + 1] +
            micro_subtasks +
            task.subtasks[stuck_index + 1:]
        )
        
        # Re-number orders
        for idx, st in enumerate(task.subtasks):
            st.order = idx
        
        # Save updated task
        self._update_task(task)
        
        return task
    
    # ========================================================================
    # PATTERN STORAGE
    # ========================================================================
    
    def _store_pattern(self, task_id: str, pattern_type: str, data: Dict[str, Any]):
        """Store completion patterns for future personalization"""
        pattern_id = f"{task_id}_{pattern_type}_{datetime.now().timestamp()}"
        
        document = json.dumps(data)
        metadata = {
            "task_id": task_id,
            "pattern_type": pattern_type,
            "timestamp": datetime.now().isoformat()
        }
        # Add simple types only
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
        
        self.patterns_collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[pattern_id]
        )
    
    def get_user_patterns(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """Retrieve user's task completion patterns"""
        result = self.patterns_collection.get()
        
        patterns = result['metadatas']
        
        if pattern_type:
            patterns = [p for p in patterns if p.get('pattern_type') == pattern_type]
        
        return patterns
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of today's task activity"""
        all_tasks = self.get_all_tasks()
        
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
        in_progress = len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS])
        
        # Calculate subtask stats
        total_subtasks = sum(len(t.subtasks) for t in all_tasks)
        completed_subtasks = sum(
            len([st for st in t.subtasks if st.status == TaskStatus.COMPLETED])
            for t in all_tasks
        )
        
        # Calculate time spent today
        total_minutes = sum(
            sum(st.time_spent_minutes for st in t.subtasks)
            for t in all_tasks
        )
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress,
            "total_subtasks": total_subtasks,
            "completed_subtasks": completed_subtasks,
            "completion_rate": (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0,
            "total_time_minutes": total_minutes,
            "average_task_progress": sum(t.get_progress() for t in all_tasks) / len(all_tasks) if all_tasks else 0
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demo the task manager"""
        # Initialize
        tm = TaskManager()
        
        # Break down a big task
        print("🔨 Breaking down task...")
        task = await tm.breakdown_task(
            title="Build NEXUS ADHD Assistant",
            description="Create a complete ADHD productivity app with screen monitoring, emotion detection, and smart task scheduling",
            priority=TaskPriority.HIGH,
            context="This will help thousands of people with ADHD be more productive and less stressed",
            tags=["coding", "adhd", "productivity"]
        )
        
        print(f"\n✅ Task broken into {len(task.subtasks)} subtasks:")
        for st in task.subtasks:
            print(f"  {st.order + 1}. {st.title} ({st.estimated_minutes}min) [{st.requires_state.value if st.requires_state else 'any'}]")
        
        # Get next best subtask
        print("\n🎯 Getting next best subtask for FOCUSED state...")
        next_task = tm.get_next_best_subtask(current_state=CognitiveState.FOCUSED)
        if next_task:
            print(f"  → {next_task['subtask_title']}")
            print(f"  → {next_task['subtask_description']}")
            print(f"  → Est: {next_task['estimated_minutes']} minutes")
        
        # Simulate completion
        print("\n✅ Marking first subtask as complete...")
        first_subtask = task.subtasks[0]
        updated_task = tm.update_subtask_status(
            task_id=task.id,
            subtask_id=first_subtask.id,
            status=TaskStatus.COMPLETED,
            time_spent=25
        )
        print(f"  Progress: {updated_task.get_progress():.1f}%")
        
        # Get summary
        print("\n📊 Daily Summary:")
        summary = tm.get_daily_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
    
    # Run demo
    asyncio.run(demo())