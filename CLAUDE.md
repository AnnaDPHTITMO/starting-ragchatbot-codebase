# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the application (from project root)
cd backend && uv run uvicorn app:app --reload --port 8000

# Or use the shell script
./run.sh
```

The app runs at http://localhost:8000 with API docs at http://localhost:8000/docs

## Architecture

This is a RAG (Retrieval-Augmented Generation) chatbot for querying course materials.

### Data Flow

```
User Query → FastAPI (/api/query) → RAGSystem.query()
    → AIGenerator.generate_response() [with tools]
    → LLM decides to call search_course_content tool
    → CourseSearchTool.execute() → VectorStore.search() → ChromaDB
    → Results returned to LLM → Final response
```

### Core Components

**RAGSystem** (`backend/rag_system.py`) - Main orchestrator that wires together all components. Initializes on app startup and loads documents from `docs/` folder.

**AIGenerator** (`backend/ai_generator.py`) - LLM integration via LiteLLM. Supports multiple providers (Anthropic, OpenAI, Groq, Ollama, etc.) configured via `LLM_MODEL` env var with format `provider/model-name`.

**VectorStore** (`backend/vector_store.py`) - ChromaDB wrapper with two collections: `course_catalog` (metadata) and `course_content` (text chunks). Uses sentence-transformers for embeddings.

**SearchTools** (`backend/search_tools.py`) - OpenAI-compatible function calling tools. `CourseSearchTool` performs semantic search with optional course/lesson filtering. Tool definitions use the `{"type": "function", "function": {...}}` format.

**DocumentProcessor** (`backend/document_processor.py`) - Parses course documents with expected format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson 0: [title]
Lesson Link: [url]
[content]
```

### Configuration

All config in `backend/config.py`. Key environment variables in `.env`:
- `LLM_API_KEY` - API key for the LLM provider
- `LLM_MODEL` - Model string like `groq/llama-3.3-70b-versatile` or `ollama/llama3`

### Frontend

Static HTML/CSS/JS served from `frontend/` directory. No build step required.
