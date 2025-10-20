# Flexible Retriever System - Implementation Summary

## Overview

Successfully implemented a flexible, plug-and-play retriever architecture using the **Registry Pattern** with per-agent configuration support. The system allows easy switching between different RAG retrieval strategies without code changes.

## What Was Implemented

### ✅ Core Components

1. **Base Infrastructure**
   - `app/retrievers/types.py` - Type definitions for retriever configs
   - `app/retrievers/builder.py` - Abstract `RetrieverBuilder` base class
   - `app/retrievers/registry.py` - Registry pattern with decorator-based registration
   - `app/retrievers/qdrant_retriever.py` - LangChain `BaseRetriever` wrapper for Qdrant

2. **Concrete Retrievers**
   - `app/retrievers/builders/naive_builder.py` - Direct similarity search
   - `app/retrievers/builders/cohere_rerank_builder.py` - Two-stage retrieval with Cohere rerank

3. **Configuration System**
   - `app/retrievers/config_helper.py` - Helper to extract per-agent configs from settings
   - Updated `app/config.py` - Per-agent retriever settings

4. **Integration**
   - Updated `app/agents/review_controller_langgraph.py` - Uses registry to create retrievers
   - Updated `app/agents/clarity/clarity_agent.py` - Uses `BaseRetriever` instead of `VectorStoreService`
   - Updated `app/agents/rigor/rigor_agent.py` - Uses `BaseRetriever` instead of `VectorStoreService`

5. **Testing & Documentation**
   - `backend/test_retrievers.py` - Comprehensive test script
   - `backend/app/retrievers/README.md` - Full documentation

6. **Dependencies**
   - Updated `backend/pyproject.toml` - Added `langchain-cohere` and `cohere`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   RetrieverRegistry                         │
│  (Singleton with decorator-based registration)              │
│  - register("type_name") -> decorator                       │
│  - create(type, vector_store, config) -> BaseRetriever      │
│  - list_available() -> ["naive", "cohere_rerank"]           │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              │                            │
    ┌─────────▼──────────┐    ┌───────────▼─────────────┐
    │ NaiveRetriever     │    │ CohereRerankRetriever   │
    │ Builder            │    │ Builder                 │
    │                    │    │                         │
    │ @register("naive") │    │ @register("cohere_...")  │
    └────────────────────┘    └─────────────────────────┘
              │                            │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  QdrantRetriever           │
              │  (extends BaseRetriever)   │
              │                            │
              │  - _aget_relevant_docs()   │
              │  - Returns LangChain Docs  │
              └────────────────────────────┘
```

---

## Key Features

### 🎯 Registry Pattern
- **Zero if-else blocks**: No conditional logic to create retrievers
- **Decorator-based**: `@RetrieverRegistry.register("type_name")`
- **Auto-discovery**: Builders register themselves on import
- **Extensible**: Add new retrievers by decorating a class

### 🔧 Per-Agent Configuration
Each agent can use different retriever types and parameters:

```env
# Clarity Agent - Uses Cohere rerank
CLARITY_AGENT_RETRIEVER_TYPE=cohere_rerank
CLARITY_AGENT_RETRIEVER_K=3
CLARITY_AGENT_RETRIEVER_INITIAL_K=15

# Rigor Agent - Uses naive retrieval
RIGOR_AGENT_RETRIEVER_TYPE=naive
RIGOR_AGENT_RETRIEVER_K=5
```

### 🦜 LangChain Compatible
- Extends `langchain_core.retrievers.BaseRetriever`
- Works with `ContextualCompressionRetriever`
- Supports LCEL chains
- Emits proper events in LangGraph

### 🏗️ Builder Pattern
- Encapsulated validation
- Configurable defaults
- Type-safe configuration
- Clean separation of concerns

---

## Available Retrievers

### 1. Naive Retriever (`naive`)

**Description**: Direct similarity search using Qdrant with cosine distance

**Use Case**: Fast retrieval with high-quality embeddings

**Configuration**:
```python
{
    "k": 5,  # Number of documents to retrieve
    "doc_type": DocType.CLARITY  # Optional filter
}
```

### 2. Cohere Rerank Retriever (`cohere_rerank`)

**Description**: Two-stage retrieval pipeline
1. Retrieve `initial_k` candidates from Qdrant
2. Rerank using Cohere's API
3. Return top `k` results

**Use Case**: Better relevance for complex queries

**Configuration**:
```python
{
    "k": 3,  # Final number of documents
    "initial_k": 15,  # Candidates before reranking
    "model": "rerank-english-v3.0",
    "cohere_api_key": "...",
    "doc_type": DocType.CLARITY
}
```

**Requirements**: `COHERE_API_KEY` environment variable

---

## How to Use

### Quick Start

```python
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.builders import *  # Auto-register all builders
from app.services.vector_store import VectorStoreService

vector_store = VectorStoreService()

# Create a retriever
retriever = RetrieverRegistry.create(
    retriever_type="naive",
    vector_store=vector_store,
    config={"k": 5}
)

# Use it (LangChain compatible)
docs = await retriever.ainvoke("What are clarity guidelines?")
```

### Using Per-Agent Configuration

```python
from app.retrievers.config_helper import RetrieverConfigHelper
from app.models.schemas import DocType

# Get config for clarity agent
retriever_type = RetrieverConfigHelper.get_agent_retriever_type("clarity")
config = RetrieverConfigHelper.get_agent_retriever_config("clarity", DocType.CLARITY)

# Create retriever
retriever = RetrieverRegistry.create(retriever_type, vector_store, config)
```

### Testing

Run the test script:
```bash
cd backend
python3 test_retrievers.py
```

---

## Adding New Retrievers

### Step 1: Create Builder

```python
# app/retrievers/builders/my_retriever_builder.py

from app.retrievers.builder import RetrieverBuilder
from app.retrievers.registry import RetrieverRegistry

@RetrieverRegistry.register("my_retriever")
class MyRetrieverBuilder(RetrieverBuilder):
    def build(self, vector_store, config):
        return MyRetriever(vector_store, **config)

    def validate_config(self, config):
        if "k" not in config:
            raise ValueError("'k' is required")

    def get_default_config(self):
        return {"k": 5}
```

### Step 2: Import in `__init__.py`

```python
# app/retrievers/builders/__init__.py

from app.retrievers.builders.my_retriever_builder import MyRetrieverBuilder

__all__ = [..., "MyRetrieverBuilder"]
```

### Step 3: Use It

```python
retriever = RetrieverRegistry.create("my_retriever", vector_store, {"k": 5})
```

**That's it!** No changes needed to:
- Registry
- Agents
- Controller
- Existing retrievers

---

## Configuration Reference

### Environment Variables

```env
# ==========================================
# Global Retriever Settings
# ==========================================
DEFAULT_RETRIEVER_TYPE=naive

# ==========================================
# Per-Agent Configuration
# ==========================================

# Clarity Agent
CLARITY_AGENT_RETRIEVER_TYPE=naive
CLARITY_AGENT_RETRIEVER_K=3
CLARITY_AGENT_RETRIEVER_INITIAL_K=15

# Rigor Agent
RIGOR_AGENT_RETRIEVER_TYPE=naive
RIGOR_AGENT_RETRIEVER_K=3
RIGOR_AGENT_RETRIEVER_INITIAL_K=15

# Integrity Agent (future)
INTEGRITY_AGENT_RETRIEVER_TYPE=naive
INTEGRITY_AGENT_RETRIEVER_K=3
INTEGRITY_AGENT_RETRIEVER_INITIAL_K=15

# ==========================================
# Cohere Rerank Configuration
# ==========================================
COHERE_API_KEY=your_cohere_api_key_here
COHERE_RERANK_MODEL=rerank-english-v3.0
COHERE_RERANK_INITIAL_K=20
```

---

## File Structure

```
backend/app/
├── retrievers/  (NEW)
│   ├── __init__.py
│   ├── types.py                    # Type definitions
│   ├── builder.py                  # Abstract builder base
│   ├── registry.py                 # Registry pattern implementation
│   ├── qdrant_retriever.py         # LangChain BaseRetriever wrapper
│   ├── config_helper.py            # Settings helper
│   ├── builders/
│   │   ├── __init__.py             # Auto-register builders
│   │   ├── naive_builder.py        # Naive retriever builder
│   │   └── cohere_rerank_builder.py # Cohere rerank builder
│   └── README.md                   # Documentation
├── agents/
│   ├── clarity/clarity_agent.py    # MODIFIED - Uses BaseRetriever
│   ├── rigor/rigor_agent.py        # MODIFIED - Uses BaseRetriever
│   └── review_controller_langgraph.py # MODIFIED - Uses registry
├── services/
│   └── vector_store.py             # NO CHANGES
├── config.py                       # MODIFIED - Per-agent settings
└── test_retrievers.py              # NEW - Test script
```

---

## Benefits Over Previous Approach

| Feature | Before | After |
|---------|--------|-------|
| Retriever selection | Hard-coded | Config-driven |
| Adding new retrievers | Modify agents | Add builder class |
| If-else blocks | Required | None |
| Per-agent config | Not supported | Fully supported |
| LangChain integration | Limited | Full compatibility |
| Testing different strategies | Code changes | Environment variable |
| Code coupling | Tight | Loose |
| Extensibility | Difficult | Easy |

---

## Design Principles

✅ **Open-Closed Principle**: Open for extension, closed for modification
✅ **Single Responsibility**: Each builder handles one retriever type
✅ **Dependency Inversion**: Agents depend on abstraction (`BaseRetriever`)
✅ **Don't Repeat Yourself**: Registry eliminates repetitive if-else logic
✅ **Liskov Substitution**: All retrievers are interchangeable

---

## Next Steps

### Optional Enhancements

1. **Add More Retrievers**
   - Hybrid BM25 + Vector
   - Cross-encoder reranker
   - Multi-query retriever
   - Ensemble retriever

2. **Monitoring & Metrics**
   - Track retrieval latency per retriever type
   - Log relevance scores
   - A/B test different strategies

3. **Caching**
   - Cache reranked results
   - Avoid redundant API calls

4. **Cost Tracking**
   - Monitor Cohere API usage
   - Add rate limiting

---

## Testing the Implementation

### 1. Install Dependencies

```bash
cd backend
uv pip install langchain-cohere cohere
```

### 2. Set Environment Variables

```bash
# Add to backend/.env
COHERE_API_KEY=your_api_key_here
CLARITY_AGENT_RETRIEVER_TYPE=cohere_rerank
```

### 3. Run Test Script

```bash
cd backend
python3 test_retrievers.py
```

Expected output:
- Registry information
- Naive retriever test results
- Cohere rerank retriever test results (if API key is set)

### 4. Test in Review Flow

Start the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

The controller will automatically use the retrievers based on your configuration!

---

## Troubleshooting

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'langchain_cohere'`

**Solution**: Install dependencies
```bash
cd backend
uv pip install langchain-cohere cohere
```

### API Key Errors

**Issue**: `'cohere_api_key' cannot be empty`

**Solution**: Set `COHERE_API_KEY` in `.env` when using rerank retriever

### Registration Errors

**Issue**: `Unknown retriever type`

**Solution**: Ensure builders are imported:
```python
from app.retrievers.builders import *  # This registers all builders
```

---

## Summary

✅ **Implemented**: Flexible retriever system with registry pattern
✅ **Features**: Per-agent configuration, LangChain compatible, extensible
✅ **Retrievers**: Naive (direct search) + Cohere rerank (two-stage)
✅ **Integration**: Updated agents and controller
✅ **Testing**: Comprehensive test script
✅ **Documentation**: Full README and this summary

The system is production-ready and can be easily extended with new retriever types!
