from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
from datetime import datetime

class NexusOllamaEngine:
    def __init__(self, model_name="llama3.2:3b", persist_dir="./chroma_db"):
        # Initialize Ollama LLM
        self.llm = OllamaLLM(model=model_name, base_url="http://localhost:11434")
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
        
        # Initialize/load vector store
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
            collection_name="nexus_memory"
        )
        
        # Setup RAG chain
        self.setup_rag_chain()
    
    def setup_rag_chain(self):
        """Setup retrieval-augmented generation chain (modern approach)"""
        
        prompt = ChatPromptTemplate.from_template("""You are NEXUS, an AI assistant for people with ADHD. 

Context from past sessions:
{context}

Current situation:
{question}

Provide a helpful, concise suggestion (max 2 sentences). Focus on:
- Detecting if user is stuck (no activity >2min)
- Identifying errors or blockers
- Suggesting next actionable step
- Being encouraging but not intrusive

Response:""")
        
        # Create retriever
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Modern RAG chain using LCEL (LangChain Expression Language)
        def format_docs(docs):
            return "\n\n".join([doc.page_content for doc in docs])
        
        self.rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def add_memory(self, metadata: dict):
        """Store metadata as long-term memory"""
        text = f"App: {metadata['app_name']}, Text: {metadata['ocr_text']}, Time: {metadata['timestamp']}"
        
        doc = Document(
            page_content=text,
            metadata={
                "timestamp": metadata['timestamp'],
                "app": metadata['app_name'],
                "session_id": metadata.get('session_id', 'default')
            }
        )
        
        self.vectorstore.add_documents([doc])
    
    def get_suggestion(self, metadata: dict) -> dict:
        """Generate real-time suggestion based on current metadata + RAG context"""
        
        # Build current situation query
        query = f"""
        Current app: {metadata['app_name']}
        Screen text: {metadata['ocr_text'][:200]}
        Detected issues: {metadata.get('errors', 'None')}
        Time since last activity: {metadata.get('idle_time', 0)} seconds
        """
        
        # Get RAG-enhanced response
        response = self.rag_chain.invoke(query)
        
        # Determine if notification needed
        show_notification = (
            metadata.get('idle_time', 0) > 120 or  # Stuck for 2+ min
            len(metadata.get('errors', [])) > 0     # Error detected
        )
        
        return {
            "message": response,
            "show_notification": show_notification,
            "timestamp": datetime.now().isoformat()
        }
    
    def summarize_session(self, session_id: str) -> str:
        """Generate session summary for long-term memory compression"""
        # Retrieve all docs from this session
        docs = self.vectorstore.similarity_search(
            f"session_id:{session_id}", k=20
        )
        
        session_text = "\n".join([doc.page_content for doc in docs])
        
        summary_prompt = f"Summarize this work session in 2-3 sentences:\n{session_text}"
        summary = self.llm.invoke(summary_prompt)
        
        return summary


# Initialize engine (singleton pattern)
engine = NexusOllamaEngine()

def get_suggestion(metadata: dict) -> dict:
    """Main interface for FastAPI"""
    # Add to memory
    engine.add_memory(metadata)
    
    # Get suggestion
    return engine.get_suggestion(metadata)