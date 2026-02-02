import pytest
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


class TestCourseSearchTool:
    def setup_method(self):
        self.mock_store = Mock()
        self.tool = CourseSearchTool(self.mock_store)

    def test_execute_with_valid_results(self):
        """Test that valid search results are formatted correctly"""
        self.mock_store.search.return_value = SearchResults(
            documents=["Content about MCP servers"],
            metadata=[{"course_title": "MCP Course", "lesson_number": 1}],
            distances=[0.5]
        )
        self.mock_store.get_lesson_link.return_value = "https://example.com/lesson1"

        result = self.tool.execute(query="MCP servers")

        assert "MCP Course" in result
        assert "Content about MCP servers" in result
        assert len(self.tool.last_sources) == 1
        assert self.tool.last_sources[0]["text"] == "MCP Course - Lesson 1"

    def test_execute_with_error_from_store(self):
        """Test that store errors are returned as messages"""
        self.mock_store.search.return_value = SearchResults.empty("Search error: connection failed")

        result = self.tool.execute(query="test query")

        assert "Search error" in result

    def test_execute_with_empty_results(self):
        """Test handling of no results found"""
        self.mock_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )

        result = self.tool.execute(query="nonexistent topic")

        assert "No relevant content found" in result

    def test_execute_with_course_filter(self):
        """Test that course filter is passed to store"""
        self.mock_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )

        self.tool.execute(query="test", course_name="MCP")

        self.mock_store.search.assert_called_once_with(
            query="test", course_name="MCP", lesson_number=None
        )

    def test_execute_with_lesson_filter(self):
        """Test that lesson filter is passed to store"""
        self.mock_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )

        self.tool.execute(query="test", course_name="MCP", lesson_number=2)

        self.mock_store.search.assert_called_once_with(
            query="test", course_name="MCP", lesson_number=2
        )

    def test_tool_definition_format(self):
        """Test that tool definition has correct OpenAI format"""
        definition = self.tool.get_tool_definition()

        assert definition["type"] == "function"
        assert "function" in definition
        assert definition["function"]["name"] == "search_course_content"
        assert "parameters" in definition["function"]
        assert "query" in definition["function"]["parameters"]["properties"]

    def test_source_tracking_multiple_results(self):
        """Test source tracking with multiple search results"""
        self.mock_store.search.return_value = SearchResults(
            documents=["Content 1", "Content 2"],
            metadata=[
                {"course_title": "Course A", "lesson_number": 1},
                {"course_title": "Course B", "lesson_number": 3}
            ],
            distances=[0.3, 0.5]
        )
        self.mock_store.get_lesson_link.side_effect = [
            "https://example.com/a/1",
            "https://example.com/b/3"
        ]

        self.tool.execute(query="test")

        assert len(self.tool.last_sources) == 2
        assert self.tool.last_sources[0]["url"] == "https://example.com/a/1"
        assert self.tool.last_sources[1]["url"] == "https://example.com/b/3"
