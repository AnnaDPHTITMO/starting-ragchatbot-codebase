import litellm
import json
from typing import List, Optional

class AIGenerator:
    """Handles interactions with LLM APIs via LiteLLM for generating responses"""

    # Maximum sequential tool call rounds per user query
    MAX_TOOL_ROUNDS = 2

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for course information.

Tool Selection:
- **Course outline/structure questions** (e.g., "What lessons are in...", "Show me the outline of...", "What does X course cover?"): Use get_course_outline tool
- **Course content questions** (e.g., "How do I...", "Explain...", "What is...", specific concept questions): Use search_course_content tool

Tool Usage Rules:
- Use tools as needed to gather information (up to two sequential calls allowed)
- Use multiple calls when queries require comparisons, multi-part information, or data from different courses/lessons
- Synthesize results into accurate, fact-based responses
- If a tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **No meta-commentary**:
  - Provide direct answers only - no reasoning process, tool explanations, or question-type analysis
  - Do not mention "based on the search results" or "using the outline tool"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

        # Set API key in environment for LiteLLM
        # LiteLLM reads keys from environment based on provider prefix
        import os
        if api_key:
            # Map model prefixes to environment variable names
            provider_env_map = {
                "anthropic/": "ANTHROPIC_API_KEY",
                "openai/": "OPENAI_API_KEY",
                "gemini/": "GEMINI_API_KEY",
                "groq/": "GROQ_API_KEY",
                "mistral/": "MISTRAL_API_KEY",
                "openrouter/": "OPENROUTER_API_KEY",
                "cohere/": "COHERE_API_KEY",
            }
            for prefix, env_var in provider_env_map.items():
                if model.startswith(prefix):
                    os.environ[env_var] = api_key
                    break

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional multi-round tool usage.

        Supports up to MAX_TOOL_ROUNDS sequential tool calls before final response.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Build messages list (LiteLLM uses OpenAI message format)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query}
        ]

        # Track tool rounds
        tool_rounds = 0

        # Main loop for sequential tool calling
        while tool_rounds < self.MAX_TOOL_ROUNDS:
            # Build API parameters - include tools if available
            api_params = {
                **self.base_params,
                "messages": messages
            }

            if tools:
                api_params["tools"] = tools
                api_params["tool_choice"] = "auto"

            # Get response from LLM via LiteLLM
            try:
                response = litellm.completion(**api_params)
            except Exception as e:
                return f"I'm sorry, I couldn't process your request due to a service error. Please try again later. (Error: {type(e).__name__})"

            message = response.choices[0].message

            # No tool calls - return the response
            if not message.tool_calls or not tool_manager:
                return message.content

            # Process tool calls
            tool_rounds += 1

            # Add assistant's response with tool calls to messages
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool call and add results
            for tool_call in message.tool_calls:
                tool_result = self._execute_single_tool(tool_call, tool_manager)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        # Max rounds reached - final call WITHOUT tools to force a response
        final_params = {
            **self.base_params,
            "messages": messages
        }

        try:
            final_response = litellm.completion(**final_params)
            return final_response.choices[0].message.content
        except Exception as e:
            return f"I found some information but encountered an error generating the response. Please try again. (Error: {type(e).__name__})"

    def _execute_single_tool(self, tool_call, tool_manager) -> str:
        """
        Execute a single tool call and return the result.

        Args:
            tool_call: The tool call object from LLM response
            tool_manager: Manager to execute tools

        Returns:
            Tool result string, or error message
        """
        # Parse arguments from JSON string
        try:
            tool_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            return "Error: Failed to parse tool parameters."

        # Execute the tool
        try:
            return tool_manager.execute_tool(
                tool_call.function.name,
                **tool_args
            )
        except Exception as e:
            return f"Error executing search: {type(e).__name__}"
