#!/usr/bin/env python3
"""
Configuration file for the ISRO Knowledge Base API.
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for the application."""
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b:free")
    
    # Site Configuration (for OpenRouter analytics)
    SITE_URL = os.getenv("SITE_URL", "https://vedika-isro.com")
    SITE_NAME = os.getenv("SITE_NAME", "Vedika - ISRO Knowledge Assistant")
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # ChromaDB Configuration
    CHROMADB_PATH = os.getenv("CHROMADB_PATH", "../db/chroma_db")
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return any issues."""
        issues = []
        
        if not cls.OPENROUTER_API_KEY:
            issues.append("OPENROUTER_API_KEY environment variable is required")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    @classmethod
    def get_openrouter_config(cls) -> Dict[str, str]:
        """Get OpenRouter configuration as dictionary."""
        return {
            "api_key": cls.OPENROUTER_API_KEY,
            "base_url": cls.OPENROUTER_BASE_URL,
            "model": cls.OPENROUTER_MODEL,
            "site_url": cls.SITE_URL,
            "site_name": cls.SITE_NAME
        }
