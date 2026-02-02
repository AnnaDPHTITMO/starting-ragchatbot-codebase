from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults


class Tool(ABC):
    """Abstract base class for all tools"""

    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return OpenAI-compatible tool definition for this tool (used by LiteLLM)"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass


class CourseSearchTool(Tool):
    """Tool for searching course content with semantic course name matching"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources from last search
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return OpenAI-compatible tool definition (used by LiteLLM)"""
        return {
            "type": "function",
            "function": {
                "name": "search_course_content",
                "description": "Search course materials with smart course name matching and lesson filtering",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for in the course content"
                        },
                        "course_name": {
                            "type": "string",
                            "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                        },
                        "lesson_number": {
                            "type": "integer",
                            "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        Execute the search tool with given parameters.
        
        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter
            
        Returns:
            Formatted search results or error message
        """
        
        # Use the vector store's unified search interface
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # Handle errors
        if results.error:
            return results.error
        
        # Handle empty results
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        # Format and return results
        return self._format_results(results)
    
    def _format_results(self, results: SearchResults) -> str:
        """Format search results with course and lesson context"""
        formatted = []
        sources = []  # Track sources for the UI

        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')

            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"

            # Track source for the UI with link lookup
            source_text = course_title
            source_url = None
            if lesson_num is not None:
                source_text += f" - Lesson {lesson_num}"
                # Look up the lesson link from the catalog
                source_url = self.store.get_lesson_link(course_title, lesson_num)

            sources.append({
                "text": source_text,
                "url": source_url
            })

            formatted.append(f"{header}\n{doc}")

        # Store sources for retrieval
        self.last_sources = sources

        return "\n\n".join(formatted)

class CourseOutlineTool(Tool):
    """Tool for retrieving course outline and lesson structure"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources for UI

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return OpenAI-compatible tool definition"""
        return {
            "type": "function",
            "function": {
                "name": "get_course_outline",
                "description": "Get the complete outline of a course including title, link, and all lessons with their numbers and titles. Use for questions about course structure, lesson lists, or what topics a course covers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_name": {
                            "type": "string",
                            "description": "Course title or partial name (e.g., 'MCP', 'Python Basics')"
                        }
                    },
                    "required": ["course_name"]
                }
            }
        }

    def execute(self, course_name: str) -> str:
        """
        Execute the outline tool to get course structure.

        Args:
            course_name: Course title or partial match

        Returns:
            Formatted course outline or error message
        """
        # Use fuzzy matching to resolve course name
        resolved_title = self.store._resolve_course_name(course_name)

        if not resolved_title:
            return f"No course found matching '{course_name}'."

        # Get course metadata
        all_courses = self.store.get_all_courses_metadata()
        course_metadata = next((c for c in all_courses if c.get('title') == resolved_title), None)

        if not course_metadata:
            return f"Course '{resolved_title}' metadata unavailable."

        # Track source for UI
        self.last_sources = [{
            "text": course_metadata.get('title', 'Unknown Course'),
            "url": course_metadata.get('course_link')
        }]

        return self._format_outline(course_metadata)

    def _format_outline(self, metadata: Dict[str, Any]) -> str:
        """Format course metadata into a readable outline"""
        lines = [f"Course: {metadata.get('title', 'Unknown')}"]

        if metadata.get('course_link'):
            lines.append(f"Link: {metadata.get('course_link')}")

        lessons = metadata.get('lessons', [])
        lines.append(f"Total Lessons: {len(lessons)}")

        if lessons:
            lines.append("\nLessons:")
            for lesson in lessons:
                lines.append(f"  {lesson.get('lesson_number', '?')}. {lesson.get('lesson_title', 'Untitled')}")

        return "\n".join(lines)


class ToolManager:
    """Manages available tools for the AI"""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: Tool):
        """Register any tool that implements the Tool interface"""
        tool_def = tool.get_tool_definition()
        # OpenAI format: name is nested inside "function"
        tool_name = tool_def.get("function", {}).get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    
    def get_tool_definitions(self) -> list:
        """Get all tool definitions for LiteLLM (OpenAI-compatible format)"""
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        return self.tools[tool_name].execute(**kwargs)
    
    def get_last_sources(self) -> list:
        """Get sources from the last search operation"""
        # Check all tools for last_sources attribute
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources') and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """Reset sources from all tools that track sources"""
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources'):
                tool.last_sources = []