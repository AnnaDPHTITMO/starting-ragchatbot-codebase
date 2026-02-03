"""
API endpoint tests for the RAG system FastAPI application.

Since the main app.py mounts static files that don't exist in test environments,
we create a test-specific FastAPI app with the same endpoints.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional


# Define the same Pydantic models as the main app
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


# Create test app fixture
@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system for API tests."""
    rag = Mock()
    rag.query.return_value = ("Test answer about the topic.", ["Course A - Lesson 1"])
    rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"]
    }
    rag.session_manager = Mock()
    rag.session_manager.create_session.return_value = "new-session-456"
    return rag


@pytest.fixture
def test_app(mock_rag_system):
    """Create a test FastAPI app with mocked dependencies."""
    app = FastAPI(title="Test Course Materials RAG System")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()

            answer, sources = mock_rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System API"}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the app."""
    return TestClient(test_app)


class TestQueryEndpoint:
    """Tests for the /api/query endpoint."""

    def test_query_with_session_id(self, client, mock_rag_system):
        """Test query with provided session ID."""
        response = client.post(
            "/api/query",
            json={"query": "What is machine learning?", "session_id": "existing-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Test answer about the topic."
        assert data["sources"] == ["Course A - Lesson 1"]
        assert data["session_id"] == "existing-session"
        mock_rag_system.query.assert_called_once_with("What is machine learning?", "existing-session")

    def test_query_without_session_id_creates_new_session(self, client, mock_rag_system):
        """Test query without session ID creates a new session."""
        response = client.post(
            "/api/query",
            json={"query": "Explain neural networks"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "new-session-456"
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_query_empty_query_string(self, client):
        """Test query with empty query string."""
        response = client.post(
            "/api/query",
            json={"query": ""}
        )

        # Empty string is technically valid according to the schema
        assert response.status_code == 200

    def test_query_missing_query_field(self, client):
        """Test query with missing query field returns validation error."""
        response = client.post(
            "/api/query",
            json={"session_id": "some-session"}
        )

        assert response.status_code == 422  # Validation error

    def test_query_invalid_json(self, client):
        """Test query with invalid JSON body."""
        response = client.post(
            "/api/query",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_query_returns_500_on_rag_error(self, client, mock_rag_system):
        """Test that RAG system errors return 500 status."""
        mock_rag_system.query.side_effect = Exception("Database connection failed")

        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_query_response_model_validation(self, client, mock_rag_system):
        """Test that response matches QueryResponse model."""
        response = client.post(
            "/api/query",
            json={"query": "Test"}
        )

        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert isinstance(data["sources"], list)


class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint."""

    def test_get_courses_success(self, client, mock_rag_system):
        """Test successful course stats retrieval."""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 2
        assert data["course_titles"] == ["Course A", "Course B"]

    def test_get_courses_empty_catalog(self, client, mock_rag_system):
        """Test courses endpoint with empty catalog."""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_returns_500_on_error(self, client, mock_rag_system):
        """Test that analytics errors return 500 status."""
        mock_rag_system.get_course_analytics.side_effect = Exception("Analytics failed")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "Analytics failed" in response.json()["detail"]

    def test_get_courses_response_model_validation(self, client):
        """Test that response matches CourseStats model."""
        response = client.get("/api/courses")

        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_api_info(self, client):
        """Test that root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAPIIntegration:
    """Integration tests that test multiple endpoints together."""

    def test_full_query_workflow(self, client, mock_rag_system):
        """Test a complete workflow: check courses, then make a query."""
        # First, check available courses
        courses_response = client.get("/api/courses")
        assert courses_response.status_code == 200
        assert courses_response.json()["total_courses"] > 0

        # Then make a query
        query_response = client.post(
            "/api/query",
            json={"query": "Tell me about Course A"}
        )
        assert query_response.status_code == 200
        assert query_response.json()["answer"]

    def test_multiple_queries_same_session(self, client, mock_rag_system):
        """Test multiple queries in the same session."""
        # First query creates session
        response1 = client.post(
            "/api/query",
            json={"query": "First question"}
        )
        session_id = response1.json()["session_id"]

        # Second query uses same session
        response2 = client.post(
            "/api/query",
            json={"query": "Follow up question", "session_id": session_id}
        )

        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

    def test_concurrent_queries_different_sessions(self, client, mock_rag_system):
        """Test that different sessions are handled independently."""
        response1 = client.post(
            "/api/query",
            json={"query": "Question 1", "session_id": "session-a"}
        )
        response2 = client.post(
            "/api/query",
            json={"query": "Question 2", "session_id": "session-b"}
        )

        assert response1.json()["session_id"] == "session-a"
        assert response2.json()["session_id"] == "session-b"
