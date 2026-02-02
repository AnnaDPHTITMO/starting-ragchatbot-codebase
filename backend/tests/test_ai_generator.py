import pytest
import sys
import os
import json

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator


class TestAIGenerator:
    def setup_method(self):
        self.generator = AIGenerator(api_key="test-key", model="test/model")
        self.mock_tool_manager = Mock()
        self.mock_tools = [{"type": "function", "function": {"name": "search_course_content"}}]

    @patch('ai_generator.litellm.completion')
    def test_generate_response_without_tools(self, mock_completion):
        """Test basic response generation without tool calls"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response", tool_calls=None))]
        mock_completion.return_value = mock_response

        result = self.generator.generate_response(query="Hello")

        assert result == "Test response"
        mock_completion.assert_called_once()

    @patch('ai_generator.litellm.completion')
    def test_generate_response_with_tool_call(self, mock_completion):
        """Test that tool calls are executed correctly"""
        # First call returns tool request
        tool_call_response = Mock()
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.function.name = "search_course_content"
        tool_call.function.arguments = '{"query": "MCP servers"}'
        tool_call_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call]))]

        # Second call returns final response (explicitly set tool_calls=None)
        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="Here's info about MCP", tool_calls=None))]

        mock_completion.side_effect = [tool_call_response, final_response]
        self.mock_tool_manager.execute_tool.return_value = "MCP content from search"

        result = self.generator.generate_response(
            query="Tell me about MCP",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        assert result == "Here's info about MCP"
        self.mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="MCP servers"
        )

    @patch('ai_generator.litellm.completion')
    def test_llm_api_failure_returns_error_message(self, mock_completion):
        """Test that LLM API failures return user-friendly error message"""
        mock_completion.side_effect = Exception("API rate limited")

        result = self.generator.generate_response(query="Test")

        assert "sorry" in result.lower()
        assert "error" in result.lower()

    @patch('ai_generator.litellm.completion')
    def test_invalid_json_in_tool_args_handled_gracefully(self, mock_completion):
        """Test that invalid JSON in tool arguments is handled gracefully"""
        tool_call_response = Mock()
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.function.name = "search_course_content"
        tool_call.function.arguments = 'invalid json {'
        tool_call_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call]))]

        # Second call returns final response after error (explicitly set tool_calls=None)
        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="I encountered an issue with the search.", tool_calls=None))]

        mock_completion.side_effect = [tool_call_response, final_response]

        result = self.generator.generate_response(
            query="Test",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        # Should return a response, not raise an exception
        assert result is not None

    @patch('ai_generator.litellm.completion')
    def test_tool_execution_failure_handled_gracefully(self, mock_completion):
        """Test that tool execution failures are handled gracefully"""
        tool_call_response = Mock()
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.function.name = "search_course_content"
        tool_call.function.arguments = '{"query": "test"}'
        tool_call_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call]))]

        # Second call returns final response after error (explicitly set tool_calls=None)
        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="I had trouble searching but here's what I know.", tool_calls=None))]

        mock_completion.side_effect = [tool_call_response, final_response]
        self.mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")

        result = self.generator.generate_response(
            query="Test",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        # Should return a response, not raise an exception
        assert result is not None

    @patch('ai_generator.litellm.completion')
    def test_second_llm_call_failure_returns_error_message(self, mock_completion):
        """Test that failure in follow-up LLM call returns user-friendly error"""
        # First call returns tool request
        tool_call_response = Mock()
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.function.name = "search_course_content"
        tool_call.function.arguments = '{"query": "test"}'
        tool_call_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call]))]

        # Second call fails
        mock_completion.side_effect = [tool_call_response, Exception("Second API call failed")]
        self.mock_tool_manager.execute_tool.return_value = "Search results"

        result = self.generator.generate_response(
            query="Test",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        # Should return user-friendly error message
        assert "error" in result.lower()
        assert "sorry" in result.lower()

    @patch('ai_generator.litellm.completion')
    def test_tools_passed_to_llm(self, mock_completion):
        """Test that tools are correctly passed to LLM API"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response", tool_calls=None))]
        mock_completion.return_value = mock_response

        self.generator.generate_response(
            query="Test",
            tools=self.mock_tools
        )

        # Verify tools were passed in the API call
        call_kwargs = mock_completion.call_args[1]
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == self.mock_tools
        assert call_kwargs["tool_choice"] == "auto"

    @patch('ai_generator.litellm.completion')
    def test_conversation_history_included(self, mock_completion):
        """Test that conversation history is included in system prompt"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response", tool_calls=None))]
        mock_completion.return_value = mock_response

        self.generator.generate_response(
            query="Follow up question",
            conversation_history="User: Hello\nAssistant: Hi there!"
        )

        call_kwargs = mock_completion.call_args[1]
        system_message = call_kwargs["messages"][0]
        assert "Previous conversation" in system_message["content"]
        assert "Hello" in system_message["content"]

    # ============================================================
    # Sequential Tool Calling Tests
    # ============================================================

    @patch('ai_generator.litellm.completion')
    def test_two_sequential_tool_rounds(self, mock_completion):
        """Test that two sequential tool calls are executed correctly"""
        # First call: LLM requests tool A
        tool_call_a = Mock()
        tool_call_a.id = "call_1"
        tool_call_a.function.name = "get_course_outline"
        tool_call_a.function.arguments = '{"course_name": "MCP Course"}'
        first_response = Mock()
        first_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call_a]))]

        # Second call: LLM requests tool B after seeing A's results
        tool_call_b = Mock()
        tool_call_b.id = "call_2"
        tool_call_b.function.name = "search_course_content"
        tool_call_b.function.arguments = '{"query": "MCP servers"}'
        second_response = Mock()
        second_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call_b]))]

        # Third call: LLM returns final content
        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="Here is the complete answer", tool_calls=None))]

        mock_completion.side_effect = [first_response, second_response, final_response]
        self.mock_tool_manager.execute_tool.side_effect = ["Course outline data", "Search results"]

        result = self.generator.generate_response(
            query="Find a course about MCP",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        assert result == "Here is the complete answer"
        assert mock_completion.call_count == 3
        assert self.mock_tool_manager.execute_tool.call_count == 2

    @patch('ai_generator.litellm.completion')
    def test_max_rounds_terminates_loop(self, mock_completion):
        """Test that tool calling stops after MAX_TOOL_ROUNDS"""
        def make_tool_response(call_id):
            tc = Mock()
            tc.id = call_id
            tc.function.name = "search_course_content"
            tc.function.arguments = '{"query": "test"}'
            resp = Mock()
            resp.choices = [Mock(message=Mock(content=None, tool_calls=[tc]))]
            return resp

        # LLM keeps requesting tools beyond max rounds
        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="Forced final answer", tool_calls=None))]

        # 3 responses: 2 tool rounds + 1 final (without tools)
        mock_completion.side_effect = [
            make_tool_response("call_1"),
            make_tool_response("call_2"),
            final_response
        ]
        self.mock_tool_manager.execute_tool.return_value = "Result"

        result = self.generator.generate_response(
            query="Test",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        assert result == "Forced final answer"
        # 2 tool rounds + 1 final call = 3 total
        assert mock_completion.call_count == 3
        # Exactly MAX_TOOL_ROUNDS tool executions
        assert self.mock_tool_manager.execute_tool.call_count == 2

    @patch('ai_generator.litellm.completion')
    def test_tools_passed_in_follow_up_calls(self, mock_completion):
        """Test that tools are passed in follow-up LLM calls within max rounds"""
        # First call returns tool request
        tool_call = Mock()
        tool_call.id = "call_1"
        tool_call.function.name = "search_course_content"
        tool_call.function.arguments = '{"query": "test"}'
        first_response = Mock()
        first_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call]))]

        # Second call returns content (no more tools needed)
        second_response = Mock()
        second_response.choices = [Mock(message=Mock(content="Answer", tool_calls=None))]

        mock_completion.side_effect = [first_response, second_response]
        self.mock_tool_manager.execute_tool.return_value = "Results"

        self.generator.generate_response(
            query="Test",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        # Verify second call includes tools (still within max rounds)
        second_call_kwargs = mock_completion.call_args_list[1][1]
        assert "tools" in second_call_kwargs
        assert second_call_kwargs["tools"] == self.mock_tools

    @patch('ai_generator.litellm.completion')
    def test_final_call_after_max_rounds_excludes_tools(self, mock_completion):
        """Test that final call after max rounds does not include tools"""
        def make_tool_response(call_id):
            tc = Mock()
            tc.id = call_id
            tc.function.name = "search_course_content"
            tc.function.arguments = '{"query": "test"}'
            resp = Mock()
            resp.choices = [Mock(message=Mock(content=None, tool_calls=[tc]))]
            return resp

        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="Final", tool_calls=None))]

        mock_completion.side_effect = [
            make_tool_response("call_1"),
            make_tool_response("call_2"),
            final_response
        ]
        self.mock_tool_manager.execute_tool.return_value = "Result"

        self.generator.generate_response(
            query="Test",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        # Final call (3rd) should NOT have tools
        final_call_kwargs = mock_completion.call_args_list[2][1]
        assert "tools" not in final_call_kwargs

    @patch('ai_generator.litellm.completion')
    def test_messages_accumulate_across_rounds(self, mock_completion):
        """Test that message history is correctly built across tool rounds"""
        # First tool call
        tool_call_a = Mock()
        tool_call_a.id = "call_1"
        tool_call_a.function.name = "get_course_outline"
        tool_call_a.function.arguments = '{"course_name": "Test"}'
        first_response = Mock()
        first_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call_a]))]

        # Second tool call
        tool_call_b = Mock()
        tool_call_b.id = "call_2"
        tool_call_b.function.name = "search_course_content"
        tool_call_b.function.arguments = '{"query": "topic"}'
        second_response = Mock()
        second_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call_b]))]

        # Final response
        final_response = Mock()
        final_response.choices = [Mock(message=Mock(content="Done", tool_calls=None))]

        mock_completion.side_effect = [first_response, second_response, final_response]
        self.mock_tool_manager.execute_tool.side_effect = ["Outline", "Content"]

        self.generator.generate_response(
            query="Test query",
            tools=self.mock_tools,
            tool_manager=self.mock_tool_manager
        )

        # Check final call has accumulated messages
        final_call_kwargs = mock_completion.call_args_list[2][1]
        messages = final_call_kwargs["messages"]

        # Should have: system, user, assistant+tool_calls, tool_result, assistant+tool_calls, tool_result
        assert len(messages) == 6
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "tool"
        assert messages[4]["role"] == "assistant"
        assert messages[5]["role"] == "tool"
