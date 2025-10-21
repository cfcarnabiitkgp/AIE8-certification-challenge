# RAG Retriever Performance Comparison Tables

## CLARITY Agent: Retriever Configuration Comparison

| Retriever Configuration | K Value | Answer Relevancy | Context Precision | Context Recall | Faithfulness |
|------------------------|---------|------------------|-------------------|----------------|--------------|
| Naive | 8 | 0.0753 | 0.1250 | 1.0000 | 0.1000 |
| Naive | 10 | 0.1885 | 0.1000 | 1.0000 | 0.0000 |
| BM25 | 8 | 0.0000 | 0.0000 | 0.0000 | 0.3000 |
| BM25 | 10 | 0.0771 | 0.0000 | 0.0000 | 0.3000 |
| Cohere Rerank (initial=20) | 8 | 0.6380 | 0.1700 | 0.3000 | 0.0000 |
| Cohere Rerank (initial=20) | 10 | 0.6721 | 0.2600 | 0.4000 | 0.0000 |

### CLARITY Agent: Performance Improvements vs Naive Baseline (k=8)

| Retriever Configuration | K Value | Answer Relevancy | Context Precision | Context Recall |
|------------------------|---------|------------------|-------------------|----------------|
| Naive | 10 | +150.3% | -20.0% | 0.0% |
| BM25 | 8 | -100.0% | -100.0% | -100.0% |
| BM25 | 10 | +2.4% | -100.0% | -100.0% |
| Cohere Rerank (initial=20) | 8 | +747.2% | +36.0% | -70.0% |
| Cohere Rerank (initial=20) | 10 | +792.7% | +108.0% | -60.0% |

---

## RIGOR Agent: Retriever Configuration Comparison

| Retriever Configuration | K Value | Answer Relevancy | Context Precision | Context Recall | Faithfulness |
|------------------------|---------|------------------|-------------------|----------------|--------------|
| Naive | 8 | 0.7436 | 0.2500 | 1.0000 | 0.0000 |
| Naive | 10 | 0.7436 | 0.2300 | 1.0000 | 0.0000 |
| BM25 | 8 | 0.7436 | 0.1875 | 0.7000 | 0.0000 |
| BM25 | 10 | 0.7436 | 0.1800 | 0.8000 | 0.0000 |
| Cohere Rerank (initial=20) | 8 | 0.7436 | 0.3300 | 0.9000 | 0.0000 |
| Cohere Rerank (initial=20) | 10 | 0.7436 | 0.4100 | 0.9000 | 0.0000 |

### RIGOR Agent: Performance Improvements vs Naive Baseline (k=8)

| Retriever Configuration | K Value | Answer Relevancy | Context Precision | Context Recall |
|------------------------|---------|------------------|-------------------|----------------|
| Naive | 10 | 0.0% | -8.0% | 0.0% |
| BM25 | 8 | 0.0% | -25.0% | -30.0% |
| BM25 | 10 | 0.0% | -28.0% | -20.0% |
| Cohere Rerank (initial=20) | 8 | 0.0% | +32.0% | -10.0% |
| Cohere Rerank (initial=20) | 10 | 0.0% | +64.0% | -10.0% |

---

## Summary: Best Configuration by Metric

### CLARITY Agent

| Metric | Best Configuration | K Value | Score |
|--------|-------------------|---------|-------|
| Answer Relevancy | Cohere Rerank (initial=20) | 10 | 0.6721 |
| Context Precision | Cohere Rerank (initial=20) | 10 | 0.2600 |
| Context Recall | Naive | 8 or 10 | 1.0000 |
| Faithfulness | BM25 | 8 or 10 | 0.3000 |
| **Overall Winner** | **Cohere Rerank (initial=20)** | **10** | **Best balance** |

### RIGOR Agent

| Metric | Best Configuration | K Value | Score |
|--------|-------------------|---------|-------|
| Answer Relevancy | All configurations (tied) | Any | 0.7436 |
| Context Precision | Cohere Rerank (initial=20) | 10 | 0.4100 |
| Context Recall | Naive | 8 or 10 | 1.0000 |
| Faithfulness | All configurations (tied) | Any | 0.0000 |
| **Overall Winner** | **Cohere Rerank (initial=20)** | **10** | **Best balance** |

---

## Impact of K Value (8 vs 10)

### CLARITY Agent

| Retriever | Answer Relevancy (k=8→10) | Context Precision (k=8→10) | Context Recall (k=8→10) |
|-----------|---------------------------|----------------------------|------------------------|
| Naive | +150.3% | -20.0% | 0.0% |
| BM25 | N/A (both poor) | 0.0% (both zero) | 0.0% (both zero) |
| Cohere Rerank | +5.3% | +52.9% | +33.3% |

**Clarity Insight**: Increasing k from 8→10 significantly improves Cohere Rerank performance, especially context precision (+52.9%)

### RIGOR Agent

| Retriever | Answer Relevancy (k=8→10) | Context Precision (k=8→10) | Context Recall (k=8→10) |
|-----------|---------------------------|----------------------------|------------------------|
| Naive | 0.0% | -8.0% | 0.0% |
| BM25 | 0.0% | -4.0% | +14.3% |
| Cohere Rerank | 0.0% | +24.2% | 0.0% |

**Rigor Insight**: Increasing k from 8→10 with Cohere Rerank improves context precision by 24.2% while maintaining recall

---

## Key Findings

### CLARITY Agent
- **Naive RAG Performance**: Poor answer relevancy (0.0753-0.1885) despite perfect recall
- **BM25 Impact**: Complete failure on context metrics (precision and recall = 0)
- **Cohere Rerank Impact**: Dramatic 747-793% improvement in answer relevancy
- **K Value Effect**: k=10 with Cohere performs best (0.6721 relevancy, 0.26 precision)
- **Trade-off**: Accepts 60% reduction in recall for 8x better answer quality
- **Recommendation**: **Cohere Rerank with k=10** essential for usable performance

### RIGOR Agent
- **Naive RAG Performance**: Strong answer relevancy (0.7436) with perfect recall
- **BM25 Impact**: Degradation in precision and recall at all k values
- **Cohere Rerank Impact**: 32-64% improvement in precision, minimal recall loss
- **K Value Effect**: k=10 with Cohere achieves highest precision (0.41)
- **Trade-off**: Accepts 10% reduction in recall for 64% better precision
- **Recommendation**: **Cohere Rerank with k=10** for optimized precision-recall balance

### Overall Conclusion
Advanced retrieval (Cohere Rerank) significantly outperforms naive RAG for both agents, with particularly dramatic improvements for the CLARITY agent. **Setting k=10** provides better performance than k=8 across most metrics. The investment in reranking infrastructure is justified by measurable performance gains:
- **Clarity Agent**: 8x improvement in answer relevancy
- **Rigor Agent**: 64% improvement in context precision

### Recommended Configuration
**Both Agents: Cohere Rerank with k=10 and initial=20**
- Provides optimal balance of relevancy, precision, and recall
- Outperforms naive and BM25 approaches across critical metrics
- Justifies the additional computational cost with substantial quality gains
