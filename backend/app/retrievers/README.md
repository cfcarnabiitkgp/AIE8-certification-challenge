# Retriever System Documentation

## Overview

The retriever system provides a flexible, plug-and-play architecture for different RAG (Retrieval-Augmented Generation) retrieval strategies. It uses the **Registry Pattern** to eliminate if-else blocks and enable easy extensibility.

## Architecture

```
RetrieverRegistry (Singleton)
├── register_retriever(@decorator) -> Registers retriever builders
├── create() -> Creates retriever from config
└── list_available() -> Returns all registered retrievers

RetrieverBuilder (Abstract)
├── build() -> Creates the retriever instance
├── validate_config() -> Validates configuration
└── get_default_config() -> Returns default configuration

Concrete Builders:
├── NaiveRetrieverBuilder -> Direct Qdrant similarity search
└── CohereRerankRetrieverBuilder -> Two-stage retrieval with Cohere rerank
```

## Features

✅ **Registry Pattern**: Decorator-based registration, zero if-else blocks
✅ **Per-Agent Configuration**: Each agent can use different retriever types
✅ **LangChain Compatible**: Extends `langchain_core.retrievers.BaseRetriever`
✅ **Type Safe**: Strong typing with Pydantic models
✅ **Extensible**: Add new retrievers without modifying existing code

## Available Retrievers

### 1. Naive Retriever (`naive`)

Direct similarity search using Qdrant's vector database with cosine distance.

**Configuration:**
```python
{
    "k": 5,  # Number of documents to retrieve
    "doc_type": DocType.CLARITY  # Optional filter
}
```

**Use case:** Fast retrieval, good for high-quality embeddings

### 2. Cohere Rerank Retriever (`cohere_rerank`)

Two-stage retrieval pipeline:
1. **Stage 1**: Retrieve `initial_k` candidates from Qdrant
2. **Stage 2**: Rerank using Cohere's rerank API
3. Return top `k` reranked documents

**Configuration:**
```python
{
    "k": 5,  # Final number of documents
    "initial_k": 20,  # Candidates before reranking
    "model": "rerank-english-v3.0",  # Cohere model
    "cohere_api_key": "...",  # API key
    "doc_type": DocType.CLARITY  # Optional filter
}
```

**Use case:** Better relevance, especially for complex queries

## Usage

### Basic Usage

```python
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.builders import *  # Auto-register all builders
from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType

# Initialize vector store
vector_store = VectorStoreService()

# Create a naive retriever
retriever = RetrieverRegistry.create(
    retriever_type="naive",
    vector_store=vector_store,
    config={
        "k": 5,
        "doc_type": DocType.CLARITY
    }
)

# Use the retriever (LangChain compatible)
docs = await retriever.ainvoke("What are clarity guidelines?")

for doc in docs:
    print(doc.page_content)
    print(doc.metadata)
```

### Per-Agent Configuration

Configuration is managed in `app/config.py` and can be overridden via environment variables:

```env
# Clarity Agent
CLARITY_AGENT_RETRIEVER_TYPE=cohere_rerank
CLARITY_AGENT_RETRIEVER_K=3
CLARITY_AGENT_RETRIEVER_INITIAL_K=15

# Rigor Agent
RIGOR_AGENT_RETRIEVER_TYPE=naive
RIGOR_AGENT_RETRIEVER_K=5

# Cohere Configuration (shared)
COHERE_API_KEY=your_api_key_here
COHERE_RERANK_MODEL=rerank-english-v3.0
```

### Using Config Helper

```python
from app.retrievers.config_helper import RetrieverConfigHelper

# Get retriever type for an agent
retriever_type = RetrieverConfigHelper.get_agent_retriever_type("clarity")

# Get full config for an agent
config = RetrieverConfigHelper.get_agent_retriever_config("clarity", DocType.CLARITY)

# Create retriever
retriever = RetrieverRegistry.create(retriever_type, vector_store, config)
```

## Adding New Retrievers

To add a new retriever (e.g., hybrid BM25 + vector):

### Step 1: Create Builder Class

```python
# app/retrievers/builders/hybrid_builder.py

from app.retrievers.builder import RetrieverBuilder
from app.retrievers.registry import RetrieverRegistry

@RetrieverRegistry.register("hybrid")
class HybridRetrieverBuilder(RetrieverBuilder):
    """Builder for hybrid BM25 + vector retriever."""

    def build(self, vector_store, config):
        # Create your custom retriever
        return HybridRetriever(
            vector_store=vector_store,
            k=config["k"],
            bm25_weight=config.get("bm25_weight", 0.5)
        )

    def validate_config(self, config):
        if "k" not in config:
            raise ValueError("'k' is required")
        if config["k"] <= 0:
            raise ValueError("'k' must be positive")

    def get_default_config(self):
        return {
            "k": 5,
            "bm25_weight": 0.5,
            "doc_type": None
        }
```

### Step 2: Import in `__init__.py`

```python
# app/retrievers/builders/__init__.py

from app.retrievers.builders.hybrid_builder import HybridRetrieverBuilder

__all__ = [
    "NaiveRetrieverBuilder",
    "CohereRerankRetrieverBuilder",
    "HybridRetrieverBuilder",  # Add here
]
```

### Step 3: Use It

```python
# Just use the new retriever - no other code changes needed!
retriever = RetrieverRegistry.create(
    retriever_type="hybrid",
    vector_store=vector_store,
    config={"k": 5, "bm25_weight": 0.3}
)
```

## Testing

Run the test script to compare retrievers:

```bash
cd backend
python test_retrievers.py
```

This will:
- Display registered retrievers
- Test naive retriever
- Test Cohere rerank retriever (if API key is set)
- Show side-by-side comparison

## LangChain Integration

All retrievers extend `langchain_core.retrievers.BaseRetriever`, which means they:

- ✅ Support `.invoke()` and `.ainvoke()` methods
- ✅ Work with `ContextualCompressionRetriever`
- ✅ Can be used in LCEL chains
- ✅ Support streaming with `.astream_events()`
- ✅ Emit proper `on_retriever_start` events in LangGraph

Example LCEL chain:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

retriever = RetrieverRegistry.create("naive", vector_store, {"k": 3})
llm = ChatOpenAI(model="gpt-4")

prompt = ChatPromptTemplate.from_template(
    "Answer based on context:\nContext: {context}\nQuestion: {question}"
)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
)

response = await chain.ainvoke("What are clarity guidelines?")
```

## Configuration Reference

### Global Settings (config.py)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_retriever_type` | str | `"naive"` | Fallback retriever type |
| `cohere_api_key` | str | `""` | Cohere API key |
| `cohere_rerank_model` | str | `"rerank-english-v3.0"` | Cohere model |
| `cohere_rerank_initial_k` | int | `20` | Default candidates for rerank |

### Per-Agent Settings

For each agent (`clarity`, `rigor`, `integrity`):

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `{agent}_retriever_type` | str | `"naive"` | Retriever type for this agent |
| `{agent}_retriever_k` | int | `3` | Number of documents to retrieve |
| `{agent}_retriever_initial_k` | int | `15` | Candidates for rerank (if using rerank) |

## Benefits

| Feature | Factory Pattern | Registry Pattern (Current) |
|---------|----------------|----------------------------|
| Adding new retrievers | Modify factory function | Just decorate new builder class |
| Code coupling | Tight | Loose (registry auto-discovers) |
| Extensibility | Requires code changes | Zero code changes in registry |
| Type registration | Manual | Automatic (via decorator) |
| Validation | Mixed in factory | Encapsulated in builder |
| Testing | Hard to mock | Easy to mock/override builders |

## Troubleshooting

### "Unknown retriever type" error

Make sure the builder is imported in `app/retrievers/builders/__init__.py`.

### "cohere_api_key cannot be empty" error

Set `COHERE_API_KEY` in your `.env` file when using `cohere_rerank` retriever.

### Import errors

Ensure you import builders before using the registry:

```python
from app.retrievers.builders import *  # This registers all builders
```

## Future Enhancements

Potential retrievers to add:
- ✨ Hybrid BM25 + Vector retriever
- ✨ Cross-encoder reranker
- ✨ Multi-query retriever (query expansion)
- ✨ Ensemble retriever (combine multiple strategies)
- ✨ Parent-document retriever (retrieve larger context)
