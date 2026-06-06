# ClaimLens Project Plan

## 1. Project Positioning

ClaimLens is an AI Agent portfolio project for patent-domain analysis.

The goal is not to decide legal infringement. The goal is to help a user create a first draft of a patent infringement risk review by comparing product features with patent claim elements.

Portfolio message:

> I built an AI Agent that searches patent data, decomposes claims into technical elements, compares them with product features, and streams a traceable claim chart and risk report to the frontend.

## 2. Why This Project

This project fits the existing experience line:

- Previous KIPRIS and patent-data handling experience
- RAG and vector search experience from TechDocs
- Frontend strength in building usable analysis screens
- New extension into AI Agent workflows

It is stronger than a simple RAG chatbot because the output is produced through a structured workflow: search, parse, compare, evaluate, and report.

## 3. What Is a Patent Claim?

A patent claim defines the legally protected scope of an invention.

For infringement risk analysis, the important comparison target is usually the claim, not only the abstract or description. ClaimLens focuses on independent claims first because they define broad protection scope.

Example:

```text
1. A document question answering method comprising:
   receiving a user query;
   searching documents related to the query;
   generating an answer from the searched documents;
   providing the answer with source references.
```

Parsed claim elements:

- Element A: receives a user query
- Element B: searches related documents
- Element C: generates an answer from searched documents
- Element D: provides answer with source references

The product description is then decomposed into product features and compared against each claim element.

## 4. Data Strategy

Use both pre-collected data and live enrichment.

### Pre-collected KIPRIS Dataset

Use KIPRIS to collect a focused patent dataset by technical domain.

Initial target domains:

- RAG and document search
- AI search and recommendation
- OCR and document processing
- AI chatbot or agent workflow
- Knowledge-base question answering

Store:

- Patent metadata
- Abstract
- Applicant
- Application number
- Publication number
- Filing date
- IPC/CPC
- Claims
- Source URL

### PostgreSQL

Use PostgreSQL for durable source data and analysis history.

Recommended tables:

```text
patents
claims
claim_elements
analysis_runs
analysis_events
claim_charts
```

### Vector DB

Use Qdrant or Pinecone for semantic retrieval.

Store embeddings for:

- Abstract
- Representative claim
- Independent claims
- Claim element chunks

### Live KIPRIS Fetch

Do not call KIPRIS for every analysis step. Use live KIPRIS calls only when:

- The patent candidate needs the latest details
- The local DB does not have claims
- The user explicitly requests a refresh

This keeps the demo fast and stable while still showing real patent-data integration.

## 5. Agent Workflow

Use LangGraph because the workflow is stateful and multi-step.

### State

The graph state should include:

- user_input
- extracted_product_features
- generated_search_queries
- patent_candidates
- selected_claims
- parsed_claim_elements
- comparison_results
- risk_scores
- claim_chart
- final_report
- events

### Nodes

1. Input Analyzer
   - Extract product features
   - Generate search queries
   - Identify technical domain

2. Patent Search
   - Run hybrid search against local patent DB
   - Search claim embeddings
   - Return top patent candidates

3. Patent Detail Fetcher
   - Load claims and metadata from PostgreSQL
   - Optionally refresh from KIPRIS

4. Claim Parser
   - Select independent claims
   - Split claims into claim elements

5. Feature Matcher
   - Compare product features with claim elements
   - Classify match status

6. Risk Evaluator
   - Assign technical risk level
   - Explain evidence and uncertainty

7. Report Writer
   - Generate claim chart
   - Generate final Markdown report

## 6. Tool Calling Plan

Tool calling is useful here even if the service does not rely only on external APIs.

Tools:

```text
search_patents(query, filters)
fetch_patent_detail(application_number)
get_claims(patent_id)
parse_claim_elements(claim_text)
extract_product_features(product_description)
compare_claim_to_features(claim_elements, product_features)
generate_claim_chart(comparison_result)
generate_report(analysis_result)
```

Internal service functions can be exposed as tools. This makes the agent workflow observable and easier to test.

## 7. Frontend UX Plan

The frontend should not be a simple chatbot.

The core UX is an analysis workspace:

- Left panel: product or technology description input
- Center panel: agent timeline
- Right panel: patent evidence and claim preview
- Bottom/result panel: claim chart and final report

### SSE Event Types

The backend streams agent progress through Server-Sent Events.

```json
{ "type": "step_started", "step": "patent_search", "message": "Searching relevant patents." }
{ "type": "tool_called", "tool": "search_patents", "input": { "query": "RAG document search" } }
{ "type": "tool_result", "tool": "search_patents", "summary": { "count": 8 } }
{ "type": "step_completed", "step": "patent_search" }
{ "type": "claim_chart_row", "data": { "claimElement": "...", "productFeature": "...", "match": "partial" } }
{ "type": "final_report", "data": { "markdown": "..." } }
```

The UI should show:

- Agent step progress
- Tool calls
- Intermediate results
- Claim chart rows as they arrive
- Final report
- Retry or refine controls

## 8. Recommended Tech Stack

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- Zustand
- EventSource for SSE

Backend:

- FastAPI
- LangGraph
- LangChain OpenAI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Qdrant or Pinecone

AI:

- GPT-4o-mini or GPT-4.1-mini for MVP
- text-embedding-3-small for embeddings

## 9. MVP Milestones

### Milestone 1: Foundation

- Monorepo setup
- Next.js frontend shell
- FastAPI backend shell
- SSE event contract
- LangGraph skeleton

### Milestone 2: Patent Dataset

- KIPRIS collector
- PostgreSQL schema
- Claim storage
- Claim embedding pipeline

### Milestone 3: Agent Analysis

- Product feature extraction
- Hybrid patent search
- Claim parsing
- Claim-feature comparison
- Risk summary

### Milestone 4: Portfolio UI

- Agent timeline
- Evidence panel
- Claim chart
- Final report preview
- Markdown/PDF export

### Milestone 5: Quality

- Backend unit tests
- Frontend component tests
- CI for frontend and backend
- Demo seed data
- Portfolio README screenshots
