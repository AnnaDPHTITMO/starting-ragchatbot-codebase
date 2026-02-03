"""
Shared test fixtures for the RAG system tests.
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_config():
    """Create a mock configuration object for testing."""
    config = Mock()
    config.CHUNK_SIZE = 500
    config.CHUNK_OVERLAP = 50
    config.CHROMA_PATH = "./test_chroma"
    config.EMBEDDING_MODEL = "test-model"
    config.MAX_RESULTS = 5
    config.LLM_API_KEY = "test-key"
    config.LLM_MODEL = "test/model"
    config.MAX_HISTORY = 10
    return config


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = Mock()
    store.search.return_value = Mock(
        documents=["Test content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.5]
    )
    store.get_lesson_link.return_value = "https://example.com/lesson1"
    store.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"]
    }
    return store


@pytest.fixture
def mock_ai_generator():
    """Create a mock AI generator."""
    generator = Mock()
    generator.generate_response.return_value = "This is a test response."
    return generator


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = Mock()
    manager.create_session.return_value = "test-session-123"
    manager.get_conversation_history.return_value = None
    return manager


@pytest.fixture
def mock_rag_system(mock_config, mock_vector_store, mock_ai_generator, mock_session_manager):
    """Create a mock RAG system with all dependencies mocked."""
    with patch('rag_system.VectorStore', return_value=mock_vector_store), \
         patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
         patch('rag_system.SessionManager', return_value=mock_session_manager), \
         patch('rag_system.DocumentProcessor'):
        from rag_system import RAGSystem
        rag = RAGSystem(mock_config)
        rag.tool_manager.get_last_sources = Mock(return_value=[
            {"text": "Test Course - Lesson 1", "url": "https://example.com/lesson1"}
        ])
        yield rag


@pytest.fixture
def sample_query_request():
    """Sample query request data."""
    return {
        "query": "What is machine learning?",
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_query_response():
    """Sample expected query response data."""
    return {
        "answer": "Machine learning is a subset of AI...",
        "sources": ["Course A - Lesson 1"],
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_course_stats():
    """Sample course statistics."""
    return {
        "total_courses": 3,
        "course_titles": ["ML Fundamentals", "Deep Learning", "NLP Basics"]
    }
