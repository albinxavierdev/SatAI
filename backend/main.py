#!/usr/bin/env python3
"""
FastAPI Backend for ISRO Knowledge Base with OpenRouter LLM Integration

This application provides a REST API for querying ISRO space data using
OpenRouter LLM and ChromaDB vector database for semantic search.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import OpenAI
import os
from pathlib import Path
import json
import logging
from datetime import datetime

# Load .env file from parent directory
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    # If python-dotenv is not installed, try to load manually
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Vedika - ISRO Satellite & Spacecraft Knowledge Base",
    description="Vedika is an intelligent AI assistant that can answer any query related to satellites and spacecraft for the Indian Space Research Organisation (ISRO). Powered by OpenRouter LLM and ChromaDB vector database.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str = Field(..., description="The question or query about ISRO data")
    max_results: int = Field(default=5, description="Maximum number of relevant results to retrieve")
    include_metadata: bool = Field(default=True, description="Include metadata in response")

class QueryResponse(BaseModel):
    answer: str
    relevant_documents: List[Dict[str, Any]]
    query: str
    timestamp: str
    model_used: str

class HealthResponse(BaseModel):
    status: str
    chromadb_connected: bool
    openrouter_configured: bool
    timestamp: str

# Global variables for clients
chroma_client = None
openrouter_client = None
collection = None

def get_environment_variables():
    """Get required environment variables."""
    return {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "site_url": os.getenv("SITE_URL", "https://vedika-isro.com"),
        "site_name": os.getenv("SITE_NAME", "Vedika - ISRO Knowledge Assistant"),
        "model": os.getenv("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b:free")
    }

def initialize_chromadb():
    """Initialize ChromaDB connection."""
    global chroma_client, collection
    
    try:
        chroma_db_path = Path("../db/chroma_db")
        if not chroma_db_path.exists():
            raise Exception("ChromaDB not found. Please run the create_chromadb.py script first.")
        
        chroma_client = chromadb.PersistentClient(
            path=str(chroma_db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Get the collection
        collection = chroma_client.get_collection("isro_data")
        logger.info("ChromaDB initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        return False

def initialize_openrouter():
    """Initialize OpenRouter client."""
    global openrouter_client
    
    try:
        env_vars = get_environment_variables()
        
        if not env_vars["openrouter_api_key"]:
            raise Exception("OPENROUTER_API_KEY environment variable not set")
        
        openrouter_client = OpenAI(
            base_url=env_vars["openrouter_base_url"],
            api_key=env_vars["openrouter_api_key"]
        )
        
        logger.info("OpenRouter client initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenRouter: {e}")
        return False

def search_chromadb(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search ChromaDB for relevant documents.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results
        
    Returns:
        List[Dict]: List of relevant documents with metadata
    """
    try:
        if not collection:
            raise Exception("ChromaDB collection not initialized")
        
        results = collection.query(
            query_texts=[query],
            n_results=max_results,
            include=["documents", "metadatas", "distances"]
        )
        
        documents = []
        for i in range(len(results['documents'][0])):
            doc = {
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": float(results['distances'][0][i])
            }
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"Error searching ChromaDB: {e}")
        return []

def generate_answer_with_context(query: str, context_docs: List[Dict[str, Any]]) -> str:
    """
    Generate answer using OpenRouter LLM with retrieved context.
    
    Args:
        query (str): User query
        context_docs (List[Dict]): Retrieved relevant documents
        
    Returns:
        str: Generated answer
    """
    try:
        if not openrouter_client:
            raise Exception("OpenRouter client not initialized")
        
        # Prepare context from retrieved documents
        context_text = ""
        for i, doc in enumerate(context_docs, 1):
            context_text += f"Document {i}:\n{doc['content']}\n"
            if doc.get('metadata'):
                context_text += f"Type: {doc['metadata'].get('data_type', 'Unknown')}\n"
                context_text += f"Name: {doc['metadata'].get('record_name', 'Unknown')}\n"
            context_text += "\n"
        
        # Create system prompt
        system_prompt = """You are Vedika, an expert AI assistant specializing in Indian Space Research Organisation (ISRO) satellites and spacecraft data. 
        
        Your expertise includes:
        - ISRO satellite missions and launches
        - Spacecraft specifications and details
        - Launch vehicle information
        - ISRO centers and facilities
        - Customer satellite programs
        
        Use the provided context to answer questions accurately and comprehensively. 
        If the context doesn't contain enough information to answer the question, 
        say so clearly. Always cite specific information from the context when possible.
        
        Remember: You are Vedika, the go-to expert for all ISRO space-related queries."""
        
        # Create user message with context
        user_message = f"""Context Information:
{context_text}

Question: {query}

As Vedika, please provide a comprehensive answer based on the context provided above. Focus on ISRO satellites, spacecraft, and space missions."""
        
        env_vars = get_environment_variables()
        
        # Make API call to OpenRouter
        completion = openrouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": env_vars["site_url"],
                "X-Title": env_vars["site_name"],
            },
            model=env_vars["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"Sorry, I encountered an error while generating the answer: {str(e)}"

def generate_fallback_answer(query: str, context_docs: List[Dict[str, Any]]) -> str:
    """
    Generate a simple fallback answer when OpenRouter is unavailable.
    Concatenates key snippets from the retrieved documents.
    """
    if not context_docs:
        return "I couldn't find any relevant information in the ISRO database for your query."

    # Take top 3 docs and synthesize a brief response
    snippets = []
    for idx, doc in enumerate(context_docs[:3], start=1):
        name = None
        if isinstance(doc.get("metadata"), dict):
            name = doc["metadata"].get("record_name")
        header = f"Source {idx}{f' - {name}' if name else ''}:"
        content = str(doc.get("content", "")).strip()
        if len(content) > 400:
            content = content[:400] + "…"
        snippets.append(f"{header}\n{content}")

    joined = "\n\n".join(snippets)
    return (
        "OpenRouter is not configured, so here is a context-based summary from the most relevant documents.\n\n"
        f"Question: {query}\n\n{joined}"
    )

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting ISRO Knowledge Base API...")
    
    # Initialize ChromaDB
    chromadb_ok = initialize_chromadb()
    
    # Initialize OpenRouter
    openrouter_ok = initialize_openrouter()
    
    if not chromadb_ok:
        logger.error("Failed to initialize ChromaDB")
    
    if not openrouter_ok:
        logger.error("Failed to initialize OpenRouter")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "ISRO Knowledge Base API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    env_vars = get_environment_variables()
    
    return HealthResponse(
        status="healthy" if chroma_client and openrouter_client else "unhealthy",
        chromadb_connected=chroma_client is not None,
        openrouter_configured=bool(env_vars["openrouter_api_key"]),
        timestamp=datetime.now().isoformat()
    )

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the ISRO knowledge base using semantic search and LLM.
    
    This endpoint:
    1. Searches the ChromaDB vector database for relevant documents
    2. Uses OpenRouter LLM to generate a comprehensive answer
    3. Returns both the answer and relevant source documents
    """
    try:
        # Validate that services are available
        if not collection:
            raise HTTPException(status_code=503, detail="ChromaDB not available")
        
        # OpenRouter may be unavailable in local/dev. We'll gracefully fallback.
        
        # Search for relevant documents
        relevant_docs = search_chromadb(request.query, request.max_results)
        
        if not relevant_docs:
            return QueryResponse(
                answer="I couldn't find any relevant information in the ISRO database for your query.",
                relevant_documents=[],
                query=request.query,
                timestamp=datetime.now().isoformat(),
                model_used=get_environment_variables()["model"]
            )
        
        # Generate answer using LLM if available; otherwise fallback
        if openrouter_client:
            answer = generate_answer_with_context(request.query, relevant_docs)
        else:
            answer = generate_fallback_answer(request.query, relevant_docs)
        
        # Prepare response documents
        response_docs = []
        for doc in relevant_docs:
            doc_response = {
                "content": doc["content"],
                "distance": doc["distance"]
            }
            
            if request.include_metadata and doc.get("metadata"):
                doc_response["metadata"] = doc["metadata"]
            
            response_docs.append(doc_response)
        
        return QueryResponse(
            answer=answer,
            relevant_documents=response_docs,
            query=request.query,
            timestamp=datetime.now().isoformat(),
            model_used=get_environment_variables()["model"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/search")
async def search_only(query: str, max_results: int = 5):
    """
    Search only endpoint - returns relevant documents without LLM processing.
    """
    try:
        if not collection:
            raise HTTPException(status_code=503, detail="ChromaDB not available")
        
        relevant_docs = search_chromadb(query, max_results)
        
        return {
            "query": query,
            "results": relevant_docs,
            "count": len(relevant_docs),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
