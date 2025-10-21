# Test Suite

This directory contains all test files for the research paper peer review system.

## Structure

```
app/tests/
├── __init__.py
├── test_agentic_system.ipynb    # Jupyter notebook testing LangGraph workflow
├── test_bm25_retriever.py       # BM25 retriever implementation tests
├── test_check_vectorstore.py    # Vector store content verification
├── test_langgraph.py            # LangGraph review controller tests
├── test_modular.py              # Modular architecture tests
├── test_notebook_parser.py      # Section parser tests
├── test_retrievers.py           # Retriever comparison tests
└── test_semantic_chunking.py    # Semantic chunking tests
```

## Running Tests

All tests should be run from the **backend root directory** (not from within `app/tests/`).

### Python Test Scripts

```bash
# From backend root directory
cd /path/to/backend

# Run individual tests
python -m app.tests.test_bm25_retriever
python -m app.tests.test_check_vectorstore
python -m app.tests.test_langgraph
python -m app.tests.test_modular
python -m app.tests.test_notebook_parser
python -m app.tests.test_retrievers
python -m app.tests.test_semantic_chunking
```

### Jupyter Notebook

```bash
# From backend root directory
cd /path/to/backend

# Launch Jupyter and open the notebook
jupyter notebook app/tests/test_agentic_system.ipynb
```

## Test Descriptions

### `test_agentic_system.ipynb`
Interactive notebook testing the complete LangGraph-based agentic system with structured Pydantic outputs.

### `test_bm25_retriever.py`
Tests the BM25 retriever implementation with various document types and queries.

### `test_check_vectorstore.py`
Verifies the Qdrant vector store contents, including document counts per type and sample queries.

### `test_langgraph.py`
Tests the LangGraph review controller with a sample quantum computing paper.

### `test_modular.py`
Tests the modular peer review architecture with clarity and rigor agents.

### `test_notebook_parser.py`
Tests the markdown section parser for extracting structured sections from research papers.

### `test_retrievers.py`
Compares different retriever types (naive, BM25, Cohere rerank) for performance evaluation.

### `test_semantic_chunking.py`
Compares semantic chunking vs fixed-size chunking for document processing.

## Import Paths

All test files are configured to properly import from the `app` module. The sys.path manipulation in each test file ensures that imports work correctly regardless of where Python is invoked from, as long as you run from the backend root.

## Requirements

- Qdrant vector database running (for vector store tests)
- Valid API keys in `.env` file:
  - `OPENAI_API_KEY` (required)
  - `COHERE_API_KEY` (optional, for rerank tests)
- All dependencies installed via `uv` or `pip`

