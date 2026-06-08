# ClaimLens Project Plan

## 1. Project Positioning

ClaimLens is an AI Agent portfolio project for patent-domain technical analysis.

The goal is not to decide legal infringement. The goal is to help a user create a first draft of a technical claim mapping review by comparing product features with patent claim elements.

Portfolio message:

> I built an AI Agent that searches patent data, decomposes claims into technical elements, compares them with product features, and streams a traceable claim chart and preliminary technical risk report to the frontend.

## 2. Why This Project

This project fits the existing experience line:

- Previous KIPRIS and patent-data handling experience
- RAG and vector search experience from TechDocs
- Frontend strength in building usable analysis screens
- New extension into AI Agent workflows

It is stronger than a simple RAG chatbot because the output is produced through a structured workflow: search, parse, compare, evaluate, and report.

## 2.1 Recommended Product Evolution

The best direction is not to replace the current patent project. The stronger strategy is to evolve the current design into a multi-agent patent analysis system.

### V1: Structured Workflow

V1 is the current foundation.

```text
Analyzer
-> Search
-> Parser
-> Matcher
-> Validator
-> Report
```

Purpose:

- Prove that patent analysis can be decomposed into clear engineering steps.
- Build the basic data path from product input to patent search, claim parsing, claim chart, and report.
- Keep the MVP implementable and testable.

Limitation:

- Even if the steps are useful, interviewers may see this as a LangGraph pipeline rather than a strong agent system.

### V2: Supervisor + Specialist Agents

V2 turns the pipeline into a role-separated multi-agent system.

```text
Supervisor Agent
├─ Search Agent
├─ Claim Agent
├─ Parsing Agent
├─ Matching Agent
├─ Validation Agent
└─ Report Agent
```

Purpose:

- Separate responsibility by analysis domain.
- Make the Supervisor Agent inspect outputs and decide the next action.
- Present the system as a multi-agent patent analysis system, not only a search service.

Supervisor examples:

```text
candidate count is low
-> rerun Search Agent with rewritten query

claim text is missing
-> run Claim Agent with KIPRIS detail enrichment

parser confidence is low
-> rerun Parsing Agent once

matched row has no evidence
-> rerun Matching Agent or downgrade through Validation Agent
```

### V3: Reflection And Recovery Loops

V3 adds reflection loops so the system can inspect weak outputs and recover.

Example:

```text
Validation Agent: "matching evidence is insufficient"
-> Supervisor Agent: "rerun Search Agent with broader query"
-> Search Agent: finds additional patent candidates
-> Claim Agent: fetches missing claims
-> Matching Agent: re-runs comparison
-> Validation Agent: checks evidence again
```

This is the version that feels the most agentic because it includes:

- Re-planning
- Self-verification
- Role separation
- Fallback
- Bounded retry
- Evidence-based downgrade

### Career Positioning

For resume and portfolio purposes, the project should be positioned as:

```text
Multi-Agent Patent Analysis System
```

This is stronger than:

```text
Patent Search Service
```

because it connects patent-domain data work with AI, data systems, workflow orchestration, and platform engineering.

### Important Caution

Do not make many agents just to increase the count. A system with 10 agents that only runs `A -> B -> C -> D` is still just a workflow with agent names.

The important design points are:

- Re-planning: the Supervisor can choose a new route when the current result is weak.
- Reflection: Validation Agent can reject weak or unsupported outputs.
- Role separation: each agent has a clear responsibility and output contract.
- Fallback: missing claims, weak parsing, low evidence, and API failure have defined recovery paths.
- Bounded autonomy: retries and live API calls are limited.

Recommended final narrative:

> I started ClaimLens as a structured patent-analysis workflow, then extended it into a bounded multi-agent system. Search, claim extraction, parsing, matching, validation, and reporting are separated into specialist agents, while a Supervisor Agent coordinates re-planning and fallback based on candidate sufficiency, claim availability, parser confidence, and evidence quality.

## 3. Interview Narrative

This project should show problem-solving ability, not only AI API usage.

Core interview story:

1. Patent documents are hard to use directly because the legally important part is the claim, not the abstract.
2. A naive RAG chatbot can retrieve related patents but cannot produce a reliable comparison structure.
3. I converted the problem into a deterministic workflow:
   - retrieve candidate patents
   - select independent claims
   - decompose claims into elements
   - extract product features
   - compare each claim element with product features
   - stream an auditable claim chart and report
4. I made the agent observable through SSE events, tool-call logs, evidence rows, and persisted analysis history.
5. I handled domain risk by clearly separating technical similarity review from legal infringement judgment.

What this proves:

- Domain understanding: claim-focused patent analysis
- Engineering judgment: structured agent workflow instead of a generic chatbot
- Backend design: stateful LangGraph pipeline, persistence, retrieval, streaming
- Frontend design: analysis workspace with progressive evidence display
- Reliability mindset: evidence, uncertainty, fallback paths, and reproducible event logs

## 4. Hard Problems To Solve

### Problem 1: Patent Search Is Not Enough

Patent search can find related documents, but related patents are not automatically meaningful for claim comparison.

Solution:

- Use hybrid retrieval over metadata, abstracts, independent claims, and claim-element chunks.
- Rank candidates by both semantic similarity and structured fields such as IPC/CPC, applicant, filing date, and keyword overlap.
- Show why each candidate was selected instead of only returning a list.

### Problem 2: Claims Are Long And Structurally Dense

Patent claims often contain nested conditions, long sentences, and dependent claim references.

Solution:

- Focus MVP on independent claims first.
- Split each independent claim into normalized claim elements.
- Preserve original claim text, parsed elements, and parser confidence.
- Allow uncertain elements to be marked instead of forcing a match.

### Problem 3: AI Matching Can Hallucinate

An LLM may overstate similarity if it is asked to produce a single final answer.

Solution:

- Compare claim elements row by row.
- Require each match result to include evidence from product features.
- Use match labels: matched, partial, not_found, uncertain.
- Generate the final report from the claim chart, not directly from a free-form prompt.

### Problem 4: Long Analysis Needs User Trust

If the backend takes time, the user must see what is happening.

Solution:

- Stream step events through SSE.
- Display tool calls, candidate patents, parsed claim elements, and claim-chart rows as they arrive.
- Persist analysis_events so a completed result can be replayed or debugged.

### Problem 5: Legal Domain Boundary

The project should not present itself as a legal infringement decision system.

Solution:

- Use "technical mapping", "preliminary review", and "uncertainty" language.
- Add a clear disclaimer in the UI and README.
- Avoid final labels such as "infringing" or "not infringing".
- Use technical risk levels only as a prioritization aid.

## 5. What Is a Patent Claim?

A patent claim defines the legally protected scope of an invention.

For technical patent review, the important comparison target is usually the claim, not only the abstract or description. ClaimLens focuses on independent claims first because they define broad protection scope.

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

## 6. Data Strategy

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

### MVP Dataset Scope

For the portfolio MVP, the dataset should be intentionally small but high-quality.

Target:

- 50-100 seed patents
- 3-5 technical domains
- At least one independent claim per patent when available
- Stored source URL for every patent
- A small set of manually inspected examples for demo quality

Fallback:

- If claims are unavailable, use abstract and representative text only for candidate search.
- Do not generate a claim chart for patents without claim text.
- Mark missing claim data clearly in the UI.

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

### Local DB vs KIPRIS Fetch Policy

The agent should not treat KIPRIS as the primary runtime database. KIPRIS is the authoritative source, but the application should use a local DB as the primary analysis store.

Default path:

```text
user input
-> generated search queries
-> local PostgreSQL keyword search + vector search
-> candidate patents
-> local claims and claim elements
-> analysis
```

Live enrichment path:

```text
candidate patent missing details
-> KIPRIS fetch by application/publication/registration number
-> normalize response
-> upsert patent and claim records
-> continue analysis
```

Use local DB first when:

- The patent already exists in `patents`.
- The claim text exists and was fetched within the freshness window.
- The analysis is running in demo mode.
- KIPRIS API quota is low or unavailable.

Use KIPRIS live fetch when:

- A candidate patent exists but claim text is missing.
- The user explicitly clicks refresh.
- The local record is older than the configured freshness window.
- The search query has too few local candidates.

Do not block the whole analysis on live fetch. If KIPRIS fails:

- Continue with available local candidates.
- Mark the candidate as `claim_unavailable` or `fetch_failed`.
- Emit an SSE `tool_error` event.
- Show the fallback reason in the evidence panel.

Freshness policy for MVP:

```text
demo_seed_data: never auto-refresh during demo
patent_metadata: refresh after 30 days
claim_text: refresh only by user request or missing data
analysis_runs: immutable once generated
```

Suggested DB fields:

```text
patents.source = kipris
patents.source_url
patents.last_fetched_at
patents.fetch_status
claims.source_document_type = publication | registration | claim_history | manual_seed
claims.raw_text
claims.normalized_text
claims.is_independent
claims.claim_number
claims.last_fetched_at
```

This design creates a clear interview point: external APIs are used as source integration, while the user-facing analysis path remains stable and reproducible.

### KIPRIS Collection Pipeline

The collection pipeline should be separate from the real-time agent flow.

1. Keyword seed collection
   - Run KIPRIS keyword search for selected domains.
   - Store application number, publication number, title, abstract, applicant, IPC/CPC, dates, and source URL.

2. Detail enrichment
   - Fetch detail records by application/publication/registration number.
   - Attach bibliographic details and available claim-related fields.

3. Claim source enrichment
   - Use `patentClaimInfo` first because it is the dedicated claim endpoint and live testing confirmed `items.claimInfo[].claim`.
   - Use `getBibliographyDetailInfoSearch` as fallback because actual samples also include `claimInfoArray.claimInfo[].claim`.
   - Try publication/registration gazette PDF data only when both claim endpoints have no claim text.
   - Use claim history data only as a supplemental source because it represents changed claims over time, not always a clean current claim set.
   - Keep `source_document_type` so the UI can explain where the claim came from.

4. Normalization
   - Remove XML/HTML artifacts.
   - Normalize whitespace and claim numbering.
   - Preserve original raw text for audit.

5. Embedding
   - Embed abstract, independent claims, and claim-element chunks.
   - Re-embed only when normalized text changes.

## 7. Agent Workflow

Use LangGraph because the workflow is stateful, multi-step, and conditional. The graph should not be a fixed linear chain. It should branch based on data availability, confidence, and validation results.

### Multi-Agent Positioning

For portfolio and interview presentation, ClaimLens should be explained as a bounded multi-agent workflow, not only as a linear LangGraph pipeline.

Recommended agent roles:

```text
Supervisor Agent
├─ Search Agent
├─ Claim Agent
├─ Parsing Agent
├─ Matching Agent
├─ Validation Agent
└─ Report Agent
```

The Supervisor Agent owns orchestration. It does not directly perform every task. Instead, it inspects each specialist agent's output and decides whether to continue, retry, downgrade, or fall back.

Supervisor decisions:

```text
search results insufficient
-> rerun Search Agent with rewritten queries
-> optionally trigger KIPRIS live enrichment

claim text missing
-> run Claim Agent with KIPRIS detail fetch
-> if still missing, mark candidate as claim_unavailable

claim parsing confidence low
-> rerun Parsing Agent once with stricter extraction
-> if still weak, keep full claim as uncertain element

matching evidence missing
-> rerun Matching Agent once
-> if evidence is still weak, Validation Agent downgrades matched to uncertain

report contains unsupported legal conclusion
-> rerun Report Agent with claim-chart-only grounding
-> remove infringement-style wording
```

This positioning makes the project stronger than a simple pipeline:

- Search Agent focuses on retrieval quality.
- Claim Agent focuses on KIPRIS detail enrichment and claim availability.
- Parsing Agent focuses on independent-claim decomposition.
- Matching Agent focuses on claim-element/product-feature comparison.
- Validation Agent focuses on evidence, allowed labels, and hallucination control.
- Report Agent summarizes only validated claim-chart rows.
- Supervisor Agent controls bounded autonomy through thresholds, retry limits, and fallback rules.

Interview message:

> I did not design ClaimLens as a single prompt or a fixed pipeline. I separated the patent analysis process into specialist agents and used a Supervisor Agent to coordinate retries and fallbacks based on search sufficiency, claim availability, parser confidence, evidence quality, and report grounding.

### State

The graph state should include:

- user_input
- extracted_product_features
- generated_search_queries
- patent_candidates
- selected_claims
- parsed_claim_elements
- comparison_results
- technical_risk_scores
- claim_chart
- final_report
- events
- errors
- retry_count
- human_review_flags

### Nodes

1. Input Analyzer
   - Extract product features
   - Generate search queries
   - Identify technical domain
   - Decide whether the input is specific enough for analysis

2. Patent Search
   - Run hybrid search against local patent DB
   - Search claim embeddings
   - Return top patent candidates
   - Decide whether local results are enough or live KIPRIS fetch is needed

3. Patent Detail Fetcher
   - Load claims and metadata from PostgreSQL
   - Optionally refresh from KIPRIS
   - Mark missing or failed claim sources without blocking the whole run

4. Claim Parser
   - Select independent claims
   - Split claims into claim elements
   - Mark parse uncertainty and preserve source spans

5. Feature Matcher
   - Compare product features with claim elements
   - Classify match status
   - Require evidence for matched and partial rows

6. Claim Chart Validator
   - Check that every row has allowed status
   - Check evidence exists for matched and partial rows
   - Send weak rows back to Feature Matcher for retry or downgrade

7. Risk Evaluator
   - Assign preliminary technical risk level
   - Explain evidence and uncertainty

8. Report Writer
   - Generate claim chart
   - Generate final Markdown report

9. Report Validator
   - Check that the report only summarizes claim-chart rows
   - Remove unsupported legal or infringement conclusions

### Conditional Edges

The workflow should include decision points so it behaves like an agentic analysis system, not a hardcoded pipeline.

```text
Input Analyzer
  -> if input is too vague: ask_for_more_detail
  -> else: Patent Search

Patent Search
  -> if local candidates >= threshold: Patent Detail Fetcher
  -> if local candidates < threshold: KIPRIS Live Fetch
  -> if no candidates: Search Query Rewriter

Patent Detail Fetcher
  -> if claim text exists: Claim Parser
  -> if claim text missing: KIPRIS Claim Fetch
  -> if fetch fails: mark candidate unavailable and continue

Claim Parser
  -> if parser confidence >= threshold: Feature Matcher
  -> if parser confidence < threshold: retry with stricter prompt
  -> if still low: keep full claim as one uncertain element

Feature Matcher
  -> Claim Chart Validator

Claim Chart Validator
  -> if rows are valid: Risk Evaluator
  -> if evidence is missing: retry Feature Matcher once
  -> if still weak: downgrade status to uncertain

Report Writer
  -> Report Validator

Report Validator
  -> if report has unsupported claims: regenerate from claim chart only
  -> else: final_report
```

### Agentic Loops

The graph should include limited loops with explicit stop conditions.

Search refinement loop:

```text
Patent Search -> Search Query Rewriter -> Patent Search
stop when:
  candidates >= threshold
  or retry_count >= 2
```

Claim parsing loop:

```text
Claim Parser -> Parser Validator -> Claim Parser
stop when:
  parser_confidence >= threshold
  or retry_count >= 1
```

Matcher validation loop:

```text
Feature Matcher -> Claim Chart Validator -> Feature Matcher
stop when:
  all matched/partial rows have evidence
  or retry_count >= 1
```

These loops make the workflow adaptive while keeping it bounded and testable.

### SSE Events For Branches

Branching decisions should be visible in the frontend.

```json
{ "type": "decision", "step": "patent_search", "message": "Local results were below threshold. Trying KIPRIS enrichment." }
{ "type": "retry", "step": "claim_parser", "message": "Parser confidence was low. Retrying with stricter extraction." }
{ "type": "fallback", "step": "claim_fetch", "message": "Claim text unavailable. Candidate excluded from claim chart." }
{ "type": "validation_failed", "step": "claim_chart_validator", "message": "Matched row had no evidence. Downgrading to uncertain." }
```

## 8. Tool Calling Plan

Tool calling is useful here even if the service does not rely only on external APIs. In this project, tools are not only "external web APIs". They are typed service capabilities that the LangGraph nodes can call and log.

The agent should use tools when it needs data access, retrieval, parsing, comparison, validation, or report generation. Each tool call should be emitted to the frontend through SSE and stored in `analysis_events`.

Tools:

```text
extract_product_features(product_description)
generate_search_queries(product_features)
search_local_patents(query, filters)
search_claim_embeddings(query, top_k)
fetch_kipris_patent_detail(application_number)
fetch_kipris_claims(application_number | publication_number | registration_number)
get_local_claims(patent_id)
normalize_claim_text(raw_claim_text)
detect_independent_claims(claims)
parse_claim_elements(claim_text)
retrieve_candidate_features(claim_element, product_features)
compare_claim_element_to_features(claim_element, product_features)
validate_claim_chart_rows(rows)
compute_preliminary_technical_risk(claim_chart)
generate_report_from_claim_chart(claim_chart)
validate_report_grounding(report, claim_chart)
```

### Tool Call Contract

Each tool should have a typed input/output contract. This makes the agent easier to test and prevents hidden prompt-only behavior.

Example:

```json
{
  "tool": "search_local_patents",
  "input": {
    "query": "document question answering vector search",
    "filters": {
      "domains": ["RAG", "document_search"],
      "date_from": "2018-01-01"
    }
  },
  "output": {
    "candidates": [
      {
        "patent_id": "pat-001",
        "application_number": "1020230000000",
        "title": "Document question answering method",
        "score": 0.82,
        "matched_fields": ["abstract", "independent_claim"]
      }
    ]
  }
}
```

### When Tools Are Called

```text
Input Analyzer:
  extract_product_features
  generate_search_queries

Patent Search:
  search_local_patents
  search_claim_embeddings
  fetch_kipris_patent_detail when local results are insufficient

Claim Fetcher:
  get_local_claims
  fetch_kipris_claims when claims are missing

Claim Parser:
  normalize_claim_text
  detect_independent_claims
  parse_claim_elements

Feature Matcher:
  retrieve_candidate_features
  compare_claim_element_to_features

Validator:
  validate_claim_chart_rows
  validate_report_grounding

Report Writer:
  compute_preliminary_technical_risk
  generate_report_from_claim_chart
```

### Why This Is Not Just A Tree

The workflow is deterministic in its safety rules, but adaptive in execution. The graph can:

- rewrite weak search queries
- switch from local DB to KIPRIS enrichment
- skip candidates with missing claims
- retry low-confidence claim parsing
- downgrade unsupported matches to uncertain
- regenerate reports that contain unsupported conclusions

This keeps the project explainable while still showing agentic decision-making.

## 9. Claim Extraction Design

Claim extraction has two different jobs:

1. Fetch or load claim text.
2. Convert claim text into comparison-ready claim elements.

### KIPRIS Claim Source Priority

Actual KIPRIS tests showed that claim text is available through the dedicated claim endpoint and also inside bibliography detail responses.

Primary source:

```text
patentClaimInfo
-> response.body.items.claimInfo[].claim
```

Fallback sources:

```text
getBibliographyDetailInfoSearch
-> response.body.item.claimInfoArray.claimInfo[].claim

getAnnFullTextInfoSearch
-> registration full-text PDF path

getPubFullTextInfoSearch
-> publication full-text PDF path
```

MVP decision:

- Do not depend on PDF text extraction for the first demo.
- Build the first claim collector around `patentClaimInfo`.
- Keep `getBibliographyDetailInfoSearch` as a fallback and metadata enrichment route.
- Store both reported `claimCount` and actual parsed `claimInfo` item count because they may differ.

Important sample finding:

```text
10-2006-0033658
reported claimCount: 8
parsed claimInfo items: 11
reason: deleted claims such as "2. 삭제" are still returned as claimInfo items
```

Therefore, deleted claims should be stored but excluded from analysis.

### Claim Selection Policy

For MVP, analyze independent claims first.

Independent claim detection:

- Prefer explicit dependency signals if the source provides them.
- Otherwise treat a claim as dependent when it references another claim, such as "according to claim 1", "the method of claim 1", or Korean equivalents like "제1항에 있어서".
- Treat claims without dependency references as independent candidates.
- If dependency detection is uncertain, mark `is_independent = null` and let the UI show "needs review".
- Exclude deleted claims such as "삭제" from claim chart generation.

Selection order:

1. Independent claim 1 if available.
2. Other independent claims in claim-number order.
3. Dependent claims only when the user expands analysis scope.

MVP default:

```text
analyze_top_n_independent_claims = 1
max_claims_per_patent = 3
max_claim_elements_per_claim = 12
```

### Claim Normalization

The parser should preserve the raw claim and create a normalized version.

Normalization rules:

- Keep claim number.
- Remove XML/HTML tags such as `<P ...>` while preserving raw text separately.
- Remove repeated spaces and line-break artifacts.
- Preserve semicolon-like separators because they often indicate elements.
- Normalize Korean claim references such as "청구항 1", "제1항".
- Do not translate claim text in MVP unless the source is already English.

Example output:

```json
{
  "claim_number": 1,
  "raw_text": "...",
  "normalized_text": "A document question answering method comprising: receiving a user query; searching documents related to the query; generating an answer...",
  "is_independent": true,
  "status": "active",
  "source_endpoint": "patentClaimInfo",
  "source_document_type": "claim_endpoint"
}
```

### Claim Element Parsing

A claim element is a comparison unit, not a legal conclusion.

Parsing strategy:

1. Rule-based pre-split
   - Split by claim separators: semicolon, numbered clauses, line breaks, "comprising", "including", "wherein".
   - For Korean claims, split around "포함하는", "단계", "수단", "부", "모듈", and semicolon-like punctuation when available.

2. LLM-assisted normalization
   - Convert split fragments into concise technical elements.
   - Keep each element grounded in the original claim text.
   - Return parser confidence and original text span when possible.

3. Validation
   - Reject empty elements.
   - Reject elements that introduce new technical features not present in the claim.
   - Limit the number of elements to avoid over-fragmentation.

Example output:

```json
{
  "claim_id": "claim-1",
  "elements": [
    {
      "element_id": "1A",
      "text": "receives a user query",
      "source_span": "receiving a user query",
      "parser_confidence": 0.94
    },
    {
      "element_id": "1B",
      "text": "searches documents related to the query",
      "source_span": "searching documents related to the query",
      "parser_confidence": 0.91
    }
  ]
}
```

Parser failure policy:

- If parsing confidence is low, keep the claim as a single element.
- Mark the claim as `parse_uncertain`.
- Continue analysis, but lower confidence in matcher output.

## 10. Feature Matcher Design

The Feature Matcher compares product features with claim elements. It should not decide infringement.

### Inputs

```text
product_features
claim_elements
candidate_patent_metadata
retrieval_evidence
```

Product feature shape:

```json
{
  "feature_id": "F1",
  "text": "The product retrieves relevant documents using vector search.",
  "source": "user_input",
  "confidence": 0.89
}
```

Claim element shape:

```json
{
  "element_id": "1B",
  "text": "searches documents related to the query",
  "source_span": "searching documents related to the query",
  "parser_confidence": 0.91
}
```

### Matching Steps

1. Candidate feature retrieval
   - For each claim element, retrieve top product features using embedding similarity and keyword overlap.

2. Pairwise comparison
   - Compare one claim element against top product features.
   - Ask the model to classify only within allowed labels.

3. Evidence validation
   - The model must quote or reference the product feature text that supports the match.
   - If no supporting feature exists, status must be `not_found` or `uncertain`.

4. Confidence scoring
   - Combine parser confidence, feature extraction confidence, retrieval similarity, and model confidence.

5. Claim chart row generation
   - Emit one row per claim element.
   - Stream each row through SSE as soon as it is ready.

### Match Status Rules

```text
matched:
  The product feature clearly covers the claim element.

partial:
  The product feature overlaps with the claim element but misses a condition, order, component, or constraint.

not_found:
  No product feature supports the claim element.

uncertain:
  The product input is ambiguous, the claim element is ambiguous, or evidence is insufficient.
```

Forbidden outputs:

```text
infringing
not_infringing
violates
safe
legal risk confirmed
```

The matcher should output technical comparison only.

### Scoring Formula For MVP

Use a simple interpretable score instead of pretending legal precision.

```text
row_confidence =
  0.30 * claim_parser_confidence
  + 0.25 * feature_extraction_confidence
  + 0.25 * retrieval_similarity
  + 0.20 * model_self_confidence
```

Patent-level preliminary technical risk:

```text
high:
  many independent claim elements are matched and few are not_found

medium:
  several elements are matched or partial, but key elements remain missing or uncertain

low:
  most elements are not_found or uncertain

insufficient_data:
  claim text is missing or parsing failed
```

This score is a prioritization signal for review, not a legal conclusion.

### Matcher Output Contract

```json
{
  "claim_element_id": "1B",
  "claim_element_text": "searches documents related to the query",
  "best_product_feature_id": "F1",
  "product_feature_text": "The product retrieves relevant documents using vector search.",
  "match_status": "matched",
  "confidence": 0.86,
  "evidence": "The product retrieves relevant documents using vector search.",
  "reasoning_summary": "Both describe retrieving documents relevant to a user query.",
  "uncertainty": "The user input does not specify whether keyword search is also used."
}
```

Quality checks:

- Every row must have one allowed `match_status`.
- `matched` and `partial` require evidence.
- `not_found` must explain what is missing.
- `uncertain` must explain why the comparison is ambiguous.
- Final report must cite claim-chart rows, not invent new matches.

## 11. Match Evaluation Contract

Each claim-chart row should be structured and testable.

```text
claim_element_id
claim_element_text
matched_product_feature
match_status: matched | partial | not_found | uncertain
confidence: 0.0 - 1.0
evidence
reasoning_summary
uncertainty
```

Rules:

- matched: the product feature clearly satisfies the claim element.
- partial: the product feature overlaps but misses a condition or detail.
- not_found: no product feature supports the claim element.
- uncertain: the input is ambiguous or the model lacks enough evidence.

The final report should summarize the claim chart instead of inventing new conclusions.

## 12. Frontend UX Plan

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

## 13. Architecture Decisions

### Why LangGraph

Use LangGraph because the workflow has explicit state, branching, and intermediate artifacts. This is more appropriate than a single chat completion because the analysis needs traceability.

### Why SSE

Use SSE because the backend mostly streams one-way progress events to the frontend. It is simpler than WebSocket for this workflow and fits step-by-step analysis output.

### Why Local Dataset First

Use a pre-collected local dataset first because live patent APIs can be slow, rate-limited, or inconsistent. Live KIPRIS fetch should enrich missing details, not block every demo.

### Why Claim Chart First

Generate the claim chart before the final report because structured rows are easier to inspect, test, and explain in interviews.

## 14. Recommended Tech Stack

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

## 15. MVP Milestones

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
- Demo seed dataset
- Missing-claim fallback handling

### Milestone 3: Agent Analysis

- Product feature extraction
- Hybrid patent search
- Claim parsing
- Claim-feature comparison
- Technical risk summary
- Match evaluation contract

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

## 16. Quality And Evaluation Plan

Backend tests:

- claim parser handles independent claim examples
- feature extractor returns stable structured output
- matcher returns allowed match_status values only
- final report references claim-chart rows
- SSE endpoint emits events in expected order

Frontend tests:

- timeline renders step_started and step_completed events
- claim chart appends streamed rows
- evidence panel shows selected patent metadata and claim text
- final report renders Markdown safely
- error and retry states are visible

Demo evaluation:

- Use 3 fixed demo product descriptions.
- Keep expected top patent candidates for each demo.
- Compare generated claim charts against manually reviewed expected rows.
- Track false overstatement cases where the model claims a stronger match than the evidence supports.

## 17. Portfolio Deliverables

The final portfolio page should include:

- Problem statement: patent analysis is claim-centric and hard to inspect manually.
- Architecture diagram: frontend, SSE API, LangGraph nodes, PostgreSQL, vector search, KIPRIS enrichment.
- Demo video or GIF: events streaming into timeline and claim chart.
- Before/after comparison: generic chatbot answer vs structured claim chart.
- Technical write-up: retrieval, claim parsing, match contract, uncertainty handling.
- GitHub README screenshots and local setup instructions.

Interview talking points:

- Why this is not a simple RAG chatbot
- How claim parsing reduces ambiguity
- How SSE improves trust during long-running analysis
- How event logs make the agent debuggable
- How legal-risk wording was controlled through product design
