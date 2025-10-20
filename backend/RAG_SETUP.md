# RAG (Retrieval-Augmented Generation) Setup Guide

This guide explains how to set up and use the vector database integration for the Clarity and Rigor agents.

## Overview

The system now uses **Qdrant vector database** to store and retrieve relevant guidelines for the Clarity and Rigor agents. This enables the agents to provide more informed, context-aware suggestions based on established writing guidelines.

## Architecture

- **Single Vector Database**: One Qdrant collection stores all documents
- **Metadata Filtering**: Uses `doc_type` enum to separate clarity, rigor, and integrity guidelines
- **Docker Volumes**: Qdrant data persists across container restarts using named volumes

## Document Types (Enum)

```python
class DocType(str, Enum):
    CLARITY = "clarity"      # Writing clarity guidelines
    RIGOR = "rigor"          # Experimental/mathematical rigor guidelines
    INTEGRITY = "integrity"  # Research integrity guidelines
    GENERAL = "general"      # General guidelines applicable to multiple areas
```

## Setup Instructions

### 1. Start Qdrant with Docker Compose

```bash
# Start all services (includes Qdrant with persistent storage)
docker-compose up -d

# Check if Qdrant is running
curl http://localhost:6333/collections
```

The `docker-compose.yml` is configured with:
- Named volume `qdrant_storage` for data persistence
- Data survives container restarts and `docker-compose down`

### 2. Upload Guidelines to Vector Database

The system includes a script to upload all PDFs from the `resources/` folder:

```bash
# Navigate to backend directory
cd backend

# Run the upload script
python -m app.scripts.upload_guidelines
```

**What this does:**
- Scans `app/resources/` folder structure
- Processes PDFs based on folder location:
  - `clarity_docs/*.pdf` → Tagged as `DocType.CLARITY`
  - `rigor_docs/*.pdf` → Tagged as `DocType.RIGOR`
  - `integrity_docs/*.pdf` → Tagged as `DocType.INTEGRITY`
  - `*.pdf` (root level) → Tagged as `DocType.GENERAL`
- Chunks each PDF (1000 chars per chunk, 200 char overlap)
- Generates embeddings using OpenAI `text-embedding-3-small`
- Stores in Qdrant with metadata

**Sample Output:**
```
Initialized VectorStoreService
Processing clarity docs from .../resources/clarity_docs
Uploading how-to-write_clear_math_paper.pdf...
✓ Uploaded 85 chunks from how-to-write_clear_math_paper.pdf
...
==================================================
UPLOAD SUMMARY
==================================================
Clarity chunks:    85
Rigor chunks:      120
Integrity chunks:  95
General chunks:    140
Total chunks:      440
Files processed:   4
==================================================
```

### 3. Verify Upload

The upload script includes automatic testing:

```bash
TESTING RETRIEVAL
==================================================

Testing CLARITY retrieval...
Found 2 clarity results:

  1. Score: 0.892
     Source: how-to-write_clear_math_paper
     Text: Always define abbreviations on first use...

Testing RIGOR retrieval...
Found 2 rigor results:

  1. Score: 0.876
     Source: knuth_mathematical_writing
     Text: Report statistical significance with p-values...
```

## How It Works

### Agent Integration

Both `ClarityAgent` and `RigorAgent` now:

1. **Accept VectorStoreService** in constructor
2. **Retrieve relevant guidelines** before analysis
3. **Enhance prompts** with retrieved context

**Example Flow (ClarityAgent):**

```python
# Step 0: Retrieve relevant guidelines (RAG)
relevant_docs = await vector_store.similarity_search(
    query=section_content[:500],  # First 500 chars as query
    k=3,                          # Top 3 most relevant docs
    doc_type=DocType.CLARITY      # Filter for clarity docs only
)

# Step 1: Enhance prompt with guidelines
guidelines_context = "\n".join([doc['text'] for doc in relevant_docs])
analysis_response = await llm.invoke(
    prompt_with_guidelines_context,
    section_content
)
```

### Metadata Filtering

Agents query only their relevant documents:

```python
# ClarityAgent retrieves ONLY clarity guidelines
await vector_store.similarity_search(
    query="text to analyze",
    doc_type=DocType.CLARITY  # Filters out rigor, integrity, general docs
)

# RigorAgent retrieves ONLY rigor guidelines
await vector_store.similarity_search(
    query="text to analyze",
    doc_type=DocType.RIGOR  # Filters out clarity, integrity, general docs
)
```

## Resources Folder Structure

```
backend/app/resources/
├── clarity_docs/
│   └── how-to-write_clear_math_paper.pdf
├── rigor_docs/
│   └── knuth_mathematical_writing.pdf
├── integrity_docs/
│   └── kretser_integrity_principles.pdf
└── primer_on_math_writing.pdf  (tagged as GENERAL)
```

## Adding New Guidelines

1. **Add PDF to appropriate folder:**
   - Clarity guidelines → `resources/clarity_docs/`
   - Rigor guidelines → `resources/rigor_docs/`
   - Integrity guidelines → `resources/integrity_docs/`
   - General guidelines → `resources/` (root)

2. **Re-run upload script:**
   ```bash
   python -m app.scripts.upload_guidelines
   ```

3. **New documents are automatically indexed** with correct metadata

## Docker Volume Management

### View Volume Data
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect qdrant_storage
```

### Backup Vector Database
```bash
# Create backup
docker run --rm -v qdrant_storage:/data -v $(pwd):/backup \
  alpine tar czf /backup/qdrant_backup.tar.gz /data
```

### Restore from Backup
```bash
# Restore backup
docker run --rm -v qdrant_storage:/data -v $(pwd):/backup \
  alpine tar xzf /backup/qdrant_backup.tar.gz -C /
```

### Reset Vector Database
```bash
# Stop containers
docker-compose down

# Remove volume (deletes all data)
docker volume rm qdrant_storage

# Recreate and re-upload
docker-compose up -d
python -m app.scripts.upload_guidelines
```

## Configuration

Environment variables in `.env`:

```env
# Qdrant Configuration
QDRANT_HOST=localhost          # Use "qdrant" in docker-compose
QDRANT_PORT=6333
QDRANT_API_KEY=                # Optional for Qdrant Cloud
QDRANT_COLLECTION_NAME=research_guidelines

# OpenAI Configuration
OPENAI_API_KEY=your_key_here
EMBEDDING_MODEL=text-embedding-3-small
```

## Troubleshooting

### Issue: "Connection refused" to Qdrant
```bash
# Check if Qdrant is running
docker-compose ps

# View Qdrant logs
docker-compose logs qdrant

# Restart Qdrant
docker-compose restart qdrant
```

### Issue: No results returned from similarity search
```bash
# Verify collection exists
curl http://localhost:6333/collections/research_guidelines

# Re-upload guidelines
python -m app.scripts.upload_guidelines
```

### Issue: "OpenAI API key not found"
```bash
# Check .env file exists
cat backend/.env | grep OPENAI_API_KEY

# Export key temporarily
export OPENAI_API_KEY="your-key-here"
```

## Performance Notes

- **Embedding Generation**: ~0.5s per chunk (OpenAI API)
- **Upload Time**: ~30-60 seconds for 400 chunks
- **Query Time**: ~100-200ms per similarity search
- **Vector Dimensions**: 1536 (OpenAI text-embedding-3-small)
- **Storage**: ~1KB per chunk (text + embedding + metadata)

## API Endpoints

The existing `/upload-guidelines` endpoint also works:

```bash
# Upload single PDF via API
curl -X POST http://localhost:8000/api/review/upload-guidelines \
  -F "file=@path/to/document.pdf"
```

## Next Steps

1. **Run the upload script** to populate your vector database
2. **Test the review endpoint** to see RAG-enhanced suggestions
3. **Add more PDFs** to `resources/` folders as needed
4. **Monitor Qdrant dashboard** at http://localhost:6333/dashboard

## References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LangChain Vector Stores](https://python.langchain.com/docs/integrations/vectorstores/qdrant)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
