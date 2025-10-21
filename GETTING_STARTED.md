# Getting Started with Research Paper Peer Review

## What is This?

An AI-powered assistant that reviews your technical research papers in real-time, using LangGraph's StateGraph workflow. It analyzes your paper with two specialized agents:

1. 📝 **Clarity Agent** - Checks writing clarity, identifies vague language, complex sentences, and undefined terms
2. 🔬 **Rigor Agent** - Validates experimental and mathematical rigor, statistical tests, and methodological soundness
3. 🎯 **Orchestrator** - Cross-validates suggestions, prioritizes important issues, and filters redundancies

The system processes papers section-by-section in a graph-based workflow for efficient, focused feedback.

## Quick Start (5 Minutes)

### Prerequisites

Make sure you have:
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ installed
- ✅ Docker installed
- ✅ OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Step 1: Start Qdrant (Vector Database)

Open a terminal and run:

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

**What's happening?** Starting a local vector database for storing and retrieving research guidelines.

Verify Qdrant is running:
```bash
docker ps  # Should show qdrant/qdrant container running
```

### Step 2: Setup Backend

Open a new terminal:

```bash
# Go to backend folder
cd backend

# Install uv if you don't have it (fast Python package manager)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create and activate virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python packages from pyproject.toml
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY=sk-...

# Start the backend server
uvicorn app.main:app --reload
```

**What's happening?** Installing the AI backend using `uv` (a fast Python package manager) and `pyproject.toml` for dependency management.

Backend will start at: `http://localhost:8000`

### Step 3: Setup Frontend

Open another terminal:

```bash
# Go to frontend folder
cd frontend

# Install Node packages
npm install

# Start the frontend
npm run dev
```

**What's happening?** Starting the web interface where you'll write and review your paper.

Frontend will start at: `http://localhost:3000`

### Step 4: Try It Out!

1. **Open your browser** to `http://localhost:3000`

2. **Copy this sample text** into the left editor:

```markdown
# Machine Learning Study

## Abstract
We made a neural network. It works good.

## Method
We used data and trained a model. Results were achieved.

## Results
Table 1 shows our results. Accuracy was high.

## Conclusion
Our method is better. Future work is needed.
```

3. **Click "Review Paper"** button

4. **Watch suggestions appear** on the right! You'll see issues like:
   - "works good" → vague language
   - Missing experimental details
   - No statistical tests
   - Missing sections (Introduction, Related Work)

## System Architecture Overview

For a detailed architecture diagram, see [`backend/architecture.png`](backend/architecture.png).

**Three Main Layers:**

1. **API Layer (FastAPI)**: Handles incoming review requests and returns suggestions
2. **Orchestration Layer (LangGraph)**: Manages workflow with state transitions
3. **Agent Layer**: Specialized agents for different analysis types
   - **ClarityAgent**: Analyzes writing clarity (all sections)
   - **RigorAgent**: Validates experimental/mathematical rigor (filtered sections)
   - **ReviewerController**: Orchestrates, validates, and prioritizes suggestions
4. **Retrieval Layer**: RAG support with multiple strategies (Naive, BM25, Cohere Rerank)
5. **External Services**: Qdrant (vector DB), OpenAI (LLMs), Cohere (reranking), Tavily (web search)

## Understanding Suggestions

Each suggestion shows:

- **Color-coded severity**:
  - 🔴 Red = Error (fix this!)
  - 🟡 Yellow = Warning (should fix)
  - 🔵 Blue = Info (consider this)

- **Category badge**: Clarity or Rigor (orchestrator validated)

- **Description**: What's wrong and why

- **Suggested fix**: How to improve it

- **Section & line numbers**: Where to look

## Customizing for Your Domain

### Add Your Own Guidelines

The system includes infrastructure for uploading conference-specific PDF guidelines to the vector database.

#### Step 1: Place your PDF guidelines

Organize your PDF files in the `backend/app/resources/` folder:

```
backend/app/resources/
├── clarity_docs/      # PDFs for clarity guidelines
├── rigor_docs/        # PDFs for rigor guidelines
├── integrity_docs/    # PDFs for integrity guidelines
└── *.pdf             # General guideline PDFs
```

#### Step 2: Upload guidelines to vector database

**Important**: Run this in a **separate terminal** while your services (from `start.sh`) are still running:

```bash
cd backend
source .venv/bin/activate
python -m app.scripts.upload_guidelines
```

**Why a separate terminal?** The `start.sh` script runs continuously in the foreground. You need to keep it running while executing the upload script in a different terminal.

The script will:
- Process all PDFs from the resources folder
- Create embeddings using OpenAI
- Upload chunks to Qdrant vector database
- Categorize by doc_type (clarity, rigor, integrity, general)
- Test retrieval to verify the upload worked

**Note**: RAG integration is not yet active in the review workflow, but the infrastructure is ready for future enhancement to provide venue-specific feedback.

## Common Questions

**Q: How much does it cost?**
A: Depends on OpenAI usage. A typical paper review costs $0.05-0.15 using gpt-4o-mini.

**Q: Is my paper sent anywhere?**
A: Only to OpenAI's API for analysis. Nothing is stored permanently (unless you modify the code).

**Q: Can I use it offline?**
A: No, it requires internet for the OpenAI API. But you can use local models with code modifications.

**Q: What formats are supported?**
A: Currently Markdown. LaTeX support is planned.

**Q: How accurate are the suggestions?**
A: They're AI-generated and should be reviewed critically. Think of it as a helpful colleague, not a final authority.

**Q: Can I modify the agents?**
A: Yes! The agents are in `backend/app/agents/clarity/` and `backend/app/agents/rigor/`. The workflow is defined in `backend/app/agents/review_controller_langgraph.py`.

## Troubleshooting

### "Connection refused" error
- Make sure all three services are running (Qdrant, backend, frontend)
- Check ports 6333, 8000, and 3000 aren't used by other apps

### "OpenAI API error"
- Verify your API key in `backend/.env`
- Check you have credits: https://platform.openai.com/usage
- Ensure internet connection is working

### "No suggestions generated"
- Check backend console for errors
- Try with shorter content first
- Verify OpenAI API is responding

### Backend won't start
```bash
# Try reinstalling dependencies
cd backend
uv pip install -e . --reinstall
```

### Frontend won't start
```bash
# Try reinstalling packages
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

### For Users
1. **Try your real paper**: Copy your actual research paper content
2. **Experiment with filters**: Filter by suggestion type or severity
3. **Upload guidelines**: Add conference-specific guidelines
4. **Iterate**: Fix suggestions and re-review

### For Developers
1. **Read ARCHITECTURE.md**: Understand the technical design
2. **Customize agents**: Modify prompts in `peer_review_graph.py`
3. **Add features**: See CONTRIBUTING.md for ideas
4. **Run tests**: Try `backend/example_test.py`

## Useful Links

- 📖 **Main Documentation**: [README.md](README.md)
- 🏗️ **LangGraph Architecture**: [MODULAR_ARCHITECTURE.md](MODULAR_ARCHITECTURE.md)
- ⚡ **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 🐳 **Docker Setup**: See `docker-compose.yml` and `start.sh`

## Example Workflow

Here's how a real research writing session might look:

1. **Draft your introduction** in the editor
2. **Click "Review Paper"**
3. **See suggestions** like "Define 'machine learning' for readers unfamiliar with the term"
4. **Revise your text** based on feedback
5. **Continue writing the next section**
6. **Review again** to see new suggestions
7. **Repeat** until you have a polished draft!

## Tips for Best Results

✅ **DO:**
- Write in clear Markdown format
- Use proper section headers (# ## ###)
- Include your complete methodology
- Write in complete sentences
- Review suggestions critically

❌ **DON'T:**
- Paste incomplete sentences or fragments
- Expect perfection on first try
- Accept all suggestions blindly
- Use as a replacement for human reviewers
- Commit `.env` files to git

## System Requirements

**Minimum:**
- 8GB RAM
- 10GB disk space (for Docker and dependencies)
- Modern browser (Chrome, Firefox, Safari, Edge)
- Stable internet connection

**Recommended:**
- 16GB RAM
- SSD storage
- Fast internet (for quicker API responses)

## Support

Found a bug? Have a question?
- Check existing documentation
- Review closed GitHub issues
- Create a new issue with details

## Privacy & Ethics

- Your paper content is sent to OpenAI for analysis
- No data is stored persistently by this application
- Be aware of your institution's policies on AI writing assistance
- Use the system to improve your writing, not to replace your thinking
- Always verify suggestions against your own judgment

---

**Ready to improve your research writing? Let's get started! 🚀**

Open `http://localhost:3000` and start writing!

