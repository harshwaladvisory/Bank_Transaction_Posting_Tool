# -*- coding: utf-8 -*-
"""
Learning Module - ChromaDB-based Self-Learning System

This module provides intelligent GL code suggestions based on:
1. ChromaDB vector similarity search (learned patterns)
2. Keyword-based fallback rules
3. User feedback learning loop

Components:
- chroma_store.py: ChromaDB operations for pattern storage
- gl_suggester.py: GL code suggestion logic
- learning_loop.py: Store and learn from user corrections
"""

from .chroma_store import ChromaLearningStore, get_chroma_store
from .gl_suggester import GLSuggester, get_gl_suggester

__all__ = [
    'ChromaLearningStore',
    'get_chroma_store',
    'GLSuggester',
    'get_gl_suggester'
]
