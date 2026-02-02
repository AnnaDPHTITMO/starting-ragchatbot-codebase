import pytest
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch, MagicMock
from rag_system import RAGSystem


class TestRAGSystem:
    def setup_method(self):
        self.mock_config = Mock()
        self.mock_config.CHUNK_SIZE = 500
        self.mock_config.CHUNK_OVERLAP = 50
        self.mock_config.CHROMA_PATH = "./test_chroma"
        self.mock_config.EMBEDDING_MODEL = "test-model"
        self.mock_config.MAX_RESULTS = 5
        self.mock_config.LLM_API_KEY = "test-key"
        self.mock_config.LLM_MODEL = "test/model"
        self.mock_config.MAX_HISTORY = 10

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_query_returns_response_and_sources(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test successful query returns response and sources"""
        mock_ai_instance = mock_ai.return_value
        mock_ai_instance.generate_response.return_value = "Test response"

        mock_sm_instance = mock_sm.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        rag = RAGSystem(self.mock_config)
        rag.tool_manager.get_last_sources = Mock(return_value=[{"text": "Source", "url": "http://example.com"}])

        response, sources = rag.query("Test query", "session-123")

        assert response == "Test response"
        assert len(sources) == 1
        mock_ai_instance.generate_response.assert_called_once()

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_query_returns_error_message_on_ai_failure(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test that AIGenerator errors result in user-friendly error messages

        With proper error handling, AIGenerator returns error messages instead of
        raising exceptions, so the query should complete successfully.
        """
        mock_ai_instance = mock_ai.return_value
        mock_ai_instance.generate_response.return_value = "I'm sorry, I couldn't process your request due to a service error."

        mock_sm_instance = mock_sm.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        rag = RAGSystem(self.mock_config)
        rag.tool_manager.get_last_sources = Mock(return_value=[])

        response, sources = rag.query("Test query", "session-123")

        assert "sorry" in response.lower()
        assert "error" in response.lower()

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_query_without_session_id(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test query works without session ID"""
        mock_ai_instance = mock_ai.return_value
        mock_ai_instance.generate_response.return_value = "Test response"

        mock_sm_instance = mock_sm.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        rag = RAGSystem(self.mock_config)
        rag.tool_manager.get_last_sources = Mock(return_value=[])

        response, sources = rag.query("Test query")

        assert response == "Test response"

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_tools_registered_on_init(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test that both tools are registered during initialization"""
        rag = RAGSystem(self.mock_config)

        # Check that both tools are registered
        tool_defs = rag.tool_manager.get_tool_definitions()
        tool_names = [t["function"]["name"] for t in tool_defs]

        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_query_passes_tools_to_ai_generator(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test that tools are passed to AIGenerator"""
        mock_ai_instance = mock_ai.return_value
        mock_ai_instance.generate_response.return_value = "Test response"

        mock_sm_instance = mock_sm.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        rag = RAGSystem(self.mock_config)
        rag.tool_manager.get_last_sources = Mock(return_value=[])

        rag.query("Test query", "session-123")

        # Verify tools were passed
        call_kwargs = mock_ai_instance.generate_response.call_args[1]
        assert "tools" in call_kwargs
        assert "tool_manager" in call_kwargs
        assert len(call_kwargs["tools"]) == 2  # Both CourseSearchTool and CourseOutlineTool

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_sources_reset_after_query(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test that sources are reset after each query"""
        mock_ai_instance = mock_ai.return_value
        mock_ai_instance.generate_response.return_value = "Test response"

        mock_sm_instance = mock_sm.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        rag = RAGSystem(self.mock_config)

        # Mock sources that get reset
        rag.tool_manager.reset_sources = Mock()
        rag.tool_manager.get_last_sources = Mock(return_value=[])

        rag.query("Test query", "session-123")

        # Verify reset was called
        rag.tool_manager.reset_sources.assert_called_once()

    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.DocumentProcessor')
    def test_session_history_updated_after_query(self, mock_dp, mock_sm, mock_ai, mock_vs):
        """Test that session history is updated after successful query"""
        mock_ai_instance = mock_ai.return_value
        mock_ai_instance.generate_response.return_value = "Test response"

        mock_sm_instance = mock_sm.return_value
        mock_sm_instance.get_conversation_history.return_value = None

        rag = RAGSystem(self.mock_config)
        rag.tool_manager.get_last_sources = Mock(return_value=[])

        rag.query("Test query", "session-123")

        # Verify history was updated
        mock_sm_instance.add_exchange.assert_called_once_with(
            "session-123", "Test query", "Test response"
        )
