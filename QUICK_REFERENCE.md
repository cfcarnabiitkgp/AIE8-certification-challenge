# Quick Reference Card

## 🚀 Start Everything

### Option 1: Quick Start Script
```bash
./start.sh
```

### Option 2: Manual Start
```bash
# 1. Start Qdrant (Terminal 1)
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 2. Start Backend (Terminal 2)
cd backend && source venv/bin/activate  # or .venv/bin/activate
uvicorn app.main:app --reload

# 3. Start Frontend (Terminal 3)
cd frontend && npm run dev
```

### Option 3: Docker Compose
```bash
docker-compose up
```

**Access**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🏗️ Architecture

**Current Implementation**: LangGraph StateGraph with Pydantic BaseModel

- **2 Agents**: Clarity + Rigor
- **Orchestrator**: Final validation and prioritization
- **Section-wise**: Concurrent per-section analysis
- **Performance**: 5-10 seconds for typical papers

## 🔧 Configuration

### Environment Variables (`backend/.env`)
```bash
OPENAI_API_KEY=sk-your-key
QDRANT_HOST=localhost
QDRANT_PORT=6333
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
```

### Token Limits (Adjust in code)
```python
# backend/app/agents/section/section_analyzer.py
SectionAnalyzer.truncate_section_content(
    section,
    max_tokens=2000  # Max tokens per section
)
```

## 🧪 Testing Commands

```bash
# Test LangGraph workflow (recommended)
cd backend
python test_langgraph.py

# Test legacy simple controller
python test_modular.py

# Test with sample paper
python test_notebook_parser.py
```

## 🌐 API Endpoints

### Analyze Paper (POST)
```bash
# LangGraph workflow (default and only option)
curl -X POST "http://localhost:8000/api/review/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Paper\n\n## Abstract\n\nText here...",
    "session_id": "session_123",
    "target_venue": "NeurIPS"
  }'
```

**Response includes**:
- `suggestions`: List of validated suggestions (Clarity + Rigor, orchestrator filtered)
- `session_id`: Session identifier
- `processing_time`: Total processing time in seconds

### Upload Guidelines (POST) - Future Feature
```bash
curl -X POST "http://localhost:8000/api/review/upload-guidelines" \
  -F "file=@guideline.pdf"
```

**Note**: Infrastructure ready but RAG not yet integrated into LangGraph workflow.

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/review/ws/session_123');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'review',
    content: '# Paper...',
    target_venue: 'NeurIPS'
  }));
};
```

### API Documentation
http://localhost:8000/docs

## 📁 Key Files

### To Customize
| File | Purpose |
|------|---------|
| `backend/app/agents/review_controller_langgraph.py` | ⭐ LangGraph workflow & nodes |
| `backend/app/agents/clarity/clarity_agent.py` | Clarity agent prompts |
| `backend/app/agents/rigor/rigor_agent.py` | Rigor agent prompts |
| `backend/app/models/schemas.py` | State & Pydantic models |
| `backend/app/config.py` | LLM settings |
| `frontend/src/components/Editor.tsx` | Editor UI |
| `frontend/src/components/SuggestionPanel.tsx` | Suggestions display |

### To Read
| File | Content |
|------|---------|
| `README.md` | Complete documentation |
| `GETTING_STARTED.md` | Setup guide |
| `MODULAR_ARCHITECTURE.md` | LangGraph implementation details |
| `QUICK_REFERENCE.md` | This file |

## 🐛 Quick Troubleshooting

### Qdrant not connecting?
```bash
docker ps                    # Check if running
docker logs <container_id>   # Check logs
```

### Backend errors?
```bash
# Check logs in terminal
# Verify .env file exists and has OPENAI_API_KEY
cat backend/.env
```

### Frontend not loading?
```bash
# Check backend is running
curl http://localhost:8000/docs

# Rebuild frontend
cd frontend && npm install && npm run dev
```

### OpenAI API errors?
- Verify API key: https://platform.openai.com/api-keys
- Check usage: https://platform.openai.com/usage
- Ensure billing is set up

## 💡 Tips

### Best Practices
✅ LangGraph workflow is the default (and recommended)
✅ Write in clear Markdown format with proper headers
✅ Include complete methodology sections
✅ Review suggestions critically (AI-generated)
✅ Check `[LangGraph]` logs for debugging

### Don't
❌ Accept all suggestions blindly
❌ Use as replacement for human review
❌ Commit `.env` files
❌ Paste incomplete fragments
❌ Expect perfection on first try

## 📊 Token Management

### Token Budget (LangGraph)
```
Per Section:      Max 2000 tokens (automatic truncation)
Per Agent Call:   ~500-1500 tokens
Orchestrator:     ~1000-2000 tokens
Total (N sections): N × 2 agents × ~1500 tokens + orchestrator
```

### Smart Filtering
```python
Clarity Agent:  All sections
Rigor Agent:    Only sections with keywords:
                - method, experiment, result, proof
                - dataset, model, evaluation
                - statistical, mathematical
                Skips: Abstract, Introduction, Conclusion, etc.
```

## 🔍 Debugging Logs

### Backend Logs Show
- `[LangGraph]` prefixed workflow execution
- Node transitions (parse → analyze → next → validate)
- Conditional edge decisions
- Section-by-section progress
- Agent suggestion counts
- Orchestrator reasoning

### Check Logs For
```bash
# LangGraph workflow
grep "\[LangGraph\]" backend_logs.txt

# State transitions
grep "Node:" backend_logs.txt

# Conditional logic
grep "Conditional:" backend_logs.txt

# Errors
grep "Error" backend_logs.txt
```

## 📈 Performance Expectations

### LangGraph Workflow (gpt-4o-mini)

| Paper Size | Sections | Time   | Cost       | Suggestions |
|------------|----------|--------|------------|-------------|
| Small      | 3-5      | 5-7s   | $0.03-0.04 | 8-15        |
| Medium     | 6-10     | 7-10s  | $0.04-0.06 | 12-25       |
| Large      | 11-15    | 10-14s | $0.06-0.08 | 18-35       |

**Note**: Orchestrator typically filters ~20-30% of suggestions for quality.

## 🔗 Useful Commands

```bash
# View API docs
open http://localhost:8000/docs

# Check Qdrant collections
curl http://localhost:6333/collections

# Check backend health
curl http://localhost:8000/

# View frontend build
cd frontend && npm run build

# Run in production
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📞 Support

1. Check documentation (README.md, GETTING_STARTED.md)
2. Review logs for errors
3. Test with simple examples first
4. Check GitHub issues
5. Create detailed bug report

## 🎯 Common Use Cases

### Academic Paper Review
```markdown
Workflow: LangGraph (default)
Target Venue: Your conference (e.g., "NeurIPS", "ICML")
Agents: Clarity + Rigor + Orchestrator
Time: 5-10 seconds
```

### Iterative Writing
```markdown
1. Write section in editor
2. Click "Review Paper"
3. Review suggestions
4. Revise based on feedback
5. Repeat for each section
```

### Pre-Submission Check
```markdown
1. Complete full draft
2. Run full review
3. Focus on ERROR severity first
4. Address WARNING severity next
5. Consider INFO suggestions
```

## 🔐 Security Checklist

- [ ] `.env` in `.gitignore`
- [ ] API key not committed
- [ ] CORS configured correctly
- [ ] Secrets manager for production
- [ ] Rate limiting enabled (if deployed)

---

**Quick Start**: `./start.sh` or `docker-compose up`

**Default Workflow**: LangGraph StateGraph ⭐

**Architecture**: 2 Agents (Clarity + Rigor) + Orchestrator Validation

**Cost Per Review**: ~$0.03-0.06 (gpt-4o-mini)

**Performance**: 5-10 seconds for typical papers
