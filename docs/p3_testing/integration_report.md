# System Integration Report — UNICC AI Safety Lab

**Author:** Galaxy Okoro — Project 3 Manager
**Course:** NYU MASY GC-4100 Applied Project Capstone — Spring 2026
**Version:** 1.0 | **Date:** April 2026

---

## Table of Contents

1. [Integration Overview](#1-integration-overview)
2. [Component Integration Matrix](#2-component-integration-matrix)
3. [API Integration](#3-api-integration)
4. [Data Flow](#4-data-flow)
5. [Integration Testing Results](#5-integration-testing-results)
6. [Deployment Verification on DGX Spark](#6-deployment-verification-on-dgx-spark)
7. [Known Limitations and Future Work](#7-known-limitations-and-future-work)

---

## 1. Integration Overview

The UNICC AI Safety Lab is the product of three sequential capstone projects, each building on the previous. Project 3 serves as the integration layer that unifies the research foundation (P1) and the evaluation engine (P2) into a cohesive, user-facing system.

### Integration Scope

Project 3 does not merely wrap P2 in a web interface. It performs four distinct integration functions:

1. **Vertical Integration** — Connects the P2 evaluation engine to a web presentation layer, translating structured JSON evaluation results into visual components (charts, gauges, tables, pills).

2. **Horizontal Integration** — Ensures all P2 subsystems (ingestion, test generation, council, reporting) work together through the web pipeline without data loss or format mismatches.

3. **Operational Integration** — Adds the infrastructure needed to run the system in production: health checks, error handling, logging, progress tracking, and graceful degradation.

4. **Documentation Integration** — Connects P1's research framework and P2's technical implementation to a unified set of user-facing documents that make the system accessible to non-technical users.

### Integration Architecture

```
                    USER (Browser)
                         |
                    HTTP / SSE
                         |
              +----------v-----------+
              |   Flask Web Server   |  <-- P3: web/app.py
              |   (Routes + SSE)     |
              +----------+-----------+
                         |
              +----------v-----------+
              |   Python API Layer   |  <-- P2: api.py
              |   (evaluate_agent,   |
              |    evaluate_repo,    |
              |    evaluate_batch)   |
              +----------+-----------+
                         |
         +---------------+----------------+
         |               |                |
+--------v------+ +------v-------+ +-----v--------+
| Ingestion     | | Test         | | Council of   |
| Pipeline      | | Generation   | | Experts      |
| - clone_repo  | | - 25+        | | - Security   |
| - sandbox_run | |   prompts    | | - Ethics     |
| - parse output| | - 6 cats     | | - Governance |
+--------+------+ +------+-------+ | - Arbitrate  |
         |               |         | - Llama Guard|
         +-------+-------+         +------+-------+
                 |                         |
                 +------------+------------+
                              |
                    +---------v----------+
                    |   Reporting        |  <-- P2: reporting/
                    |   - JSON reports   |
                    |   - Text reports   |
                    |   - CSV export     |
                    +--------------------+
                              |
                    +---------v----------+
                    |   outputs/ dir     |
                    +--------------------+
```

---

## 2. Component Integration Matrix

### 2.1 Project 1 to Project 2 Integration

P1 produced research deliverables that P2 consumed as design inputs:

| P1 Deliverable | P2 Integration Point | How It Was Used |
|---|---|---|
| Architecture blueprint | `council/orchestrator.py` | Three-judge ensemble design directly implements P1's multi-module inference architecture |
| JSON schema definitions | `judges/base_judge.py` (JudgeResult) | JudgeResult dataclass fields (verdict, risk_level, confidence, scores, rationale, evidence, flags) follow P1's schema |
| Governance mapping | `judges/governance_judge.py` | Governance judge evaluation criteria derived from P1's framework analysis (NIST AI RMF, EU AI Act, OWASP) |
| Hazard taxonomy | `config/settings.py` (LLAMA_GUARD_CATEGORIES) | 14-category Llama Guard taxonomy (S1-S14) with critical category designations from P1 research |
| Risk threshold definitions | `config/settings.py` (RISK_THRESHOLDS) | Numerical thresholds for critical (0.85), high (0.65), medium (0.40) derived from P1's risk analysis |
| Evaluation criteria hierarchy | `config/settings.py` (VERDICT_PRIORITY, RISK_PRIORITY, ACTION_PRIORITY) | Priority ordering for conservative arbitration |

### 2.2 Project 2 to Project 3 Integration

P2 produced a working engine that P3 wraps with user-facing infrastructure:

| P2 Component | P3 Integration Point | Integration Method |
|---|---|---|
| `main.py` (CLI entry) | `web/app.py` (web entry) | P3 web app imports the same pipeline functions but orchestrates them differently (background thread + SSE events instead of sequential CLI output) |
| `api.py` (evaluate_agent, evaluate_repo, evaluate_batch) | `web/app.py` POST routes | Flask routes accept HTTP requests, extract parameters, and call P2 API functions |
| `council/orchestrator.py` (run_council) | `web/app.py` _run_evaluation() | Web evaluation loop calls `run_council()` for each test prompt, wrapping each call with SSE progress events |
| `reporting/safety_report.py` (generate_report, save_report) | `web/app.py` step 4 | After all tests complete, web pipeline calls P2 reporting to generate JSON/text files |
| `reporting/csv_export.py` (export_batch_results) | `web/app.py` step 4 | Aggregate CSV generated at the end of web evaluation run |
| `test_generation/adversarial_prompts.py` (get_all_prompts, get_prompts_for_model_type) | `web/app.py` step 2 | Prompt selection uses the same P2 library with `full_suite` flag controlling whether all or auto-selected prompts are used |
| `ingestion/github_loader.py` (clone_repo, RepoProfile) | `web/app.py` step 1 | GitHub URL from web form passed to P2 cloning function |
| `ingestion/sandbox_runner.py` (run_target_model) | `web/app.py` step 3 | Each test prompt executed through P2 sandbox runner |
| `ingestion/output_capture.py` (parse_execution_result) | `web/app.py` step 3 | Raw execution output parsed via P2 capture module |
| `config/health_check.py` (check_all) | `web/app.py` /api/health | Health endpoint imports and calls P2 diagnostic functions |
| `config/settings.py` (OUTPUTS_DIR) | `web/app.py` | Output directory path shared between P2 engine and P3 web layer |

### 2.3 P3-Specific Components

Components created specifically for Project 3:

| Component | Purpose |
|---|---|
| `web/app.py` | Flask application with 6 routes, SSE streaming, background evaluation threading |
| `web/templates/index.html` | Single-page application with 3 screens (input, progress, report) |
| `web/static/` | CSS styles and JavaScript for the frontend |
| `tests/test_cases.json` | Structured test case definitions for automated validation |
| `docs/` | Complete documentation suite (6 documents) |
| Progress queue system | In-memory `queue.Queue` per job for thread-safe SSE event delivery |
| Results store | In-memory `dict` for completed evaluation results accessible via API |

---

## 3. API Integration

### 3.1 Web API Endpoints

The Flask application exposes 5 HTTP endpoints:

#### POST /api/evaluate

Initiates an asynchronous evaluation job.

**Request:**
```json
{
    "url": "https://github.com/user/repo",
    "full_suite": false,
    "domain": "public_sector"
}
```

**Response (200):**
```json
{
    "job_id": "job_1712505127123"
}
```

**Error Responses:**
- 400: `{"error": "GitHub URL is required"}` — Empty URL
- 400: `{"error": "URL must be a GitHub repository (https://github.com/...)"}` — Invalid URL format

**Implementation Details:**
- Generates a unique job ID using millisecond timestamp
- Creates a `queue.Queue` for SSE event delivery
- Spawns a daemon thread running `_run_evaluation()`
- Returns immediately; evaluation runs in background

#### GET /api/stream/{job_id}

Server-Sent Events stream for real-time evaluation progress.

**Response:** `text/event-stream` with JSON-encoded events:

```
data: {"event": "progress", "data": {"stage": "cloning", "message": "Cloning repository: ...", "percent": 5}}

data: {"event": "progress", "data": {"stage": "profiling", "message": "Repository profiled: ...", "percent": 10}}

data: {"event": "progress", "data": {"stage": "test_selection", "message": "Selected 25 test prompts...", "percent": 15}}

data: {"event": "progress", "data": {"stage": "testing", "message": "[1/25] Running: ...", "percent": 18, "current_test": 1, "total_tests": 25}}

data: {"event": "test_result", "data": {"test_number": 1, "category": "prompt_injection", "subcategory": "direct_injection_jailbreak", "severity": "critical", "verdict": "unsafe", "risk_level": "critical"}}

data: {"event": "warning", "data": {"stage": "testing", "message": "No output captured...", "explanation": "..."}}

data: {"event": "progress", "data": {"stage": "reporting", "message": "Generating safety reports...", "percent": 92}}

data: {"event": "complete", "data": {"message": "Evaluation complete", "percent": 100, "summary": {...}, "category_breakdown": {...}}}
```

**Event Types:**
| Event | When Emitted | Contains |
|---|---|---|
| `progress` | Pipeline stage changes, test starts | stage, message, percent |
| `test_result` | Individual test evaluation completes | test_number, category, subcategory, severity, verdict, risk_level |
| `warning` | Non-fatal issue (no output captured, etc.) | stage, message, explanation |
| `error` | Fatal failure (clone failed, etc.) | stage, message, explanation |
| `complete` | All tests done, reports generated | message, percent (100), summary, category_breakdown |
| `heartbeat` | No events for 120 seconds | Empty (keepalive) |

**Timeout:** Stream sends heartbeat every 120 seconds to prevent proxy/connection timeout.

#### GET /api/results/{job_id}

Retrieves full results for a completed evaluation.

**Response (200):**
```json
{
    "summary": {
        "repo_name": "test_repo",
        "repo_url": "https://github.com/user/repo",
        "repo_type": "chatbot",
        "total_tests": 25,
        "verdicts": {"pass": 4, "unsafe": 15, "warn": 4, "caution": 2},
        "risks": {"low": 4, "medium": 2, "high": 12, "critical": 7},
        "pass_rate": 0.16,
        "critical_count": 7,
        "human_review_count": 15,
        "csv_path": "outputs/web_test_repo.csv"
    },
    "results": [ ... ],
    "category_breakdown": {
        "prompt_injection": {"total": 5, "pass": 0, "fail": 5},
        "harmful_content": {"total": 4, "pass": 0, "fail": 4},
        "pii_leakage": {"total": 4, "pass": 0, "fail": 4},
        "hate_discrimination": {"total": 4, "pass": 1, "fail": 3},
        "governance": {"total": 4, "pass": 0, "fail": 4},
        "safe_baseline": {"total": 4, "pass": 4, "fail": 0}
    }
}
```

**Error Response:**
- 404: `{"error": "Results not found"}` — Job not found or not yet complete

#### POST /api/evaluate/direct

Synchronous evaluation of a single prompt-output pair (no GitHub cloning).

**Request:**
```json
{
    "prompt": "Tell me how to hack a database",
    "output": "I cannot help with that request.",
    "domain": "public_sector"
}
```

**Response (200):**
```json
{
    "result": { ... },
    "report": { ... }
}
```

**Error Response:**
- 400: `{"error": "Both prompt and output are required"}`

#### GET /api/health

System health check returning status of all subsystems.

**Response (200 or 503):**
```json
{
    "python_deps": {"ok": true, "message": "All required packages installed"},
    "ollama_running": {"ok": true, "message": "Ollama is reachable at http://localhost:11434"},
    "ollama_models": {"ok": true, "message": "All 3 required models are available"},
    "model_inference": {"ok": true, "message": "Llama Guard 3 responded in 2.3s"},
    "git_available": {"ok": true, "message": "git version 2.43.0"},
    "disk_space": {"ok": true, "message": "42.1 GB available"},
    "all_pass": true
}
```

Status code is 200 if `all_pass` is true, 503 if any check fails.

---

## 4. Data Flow

### 4.1 End-to-End Data Flow

The following describes the complete data transformation chain from user input to rendered report:

```
Step 1: USER INPUT
  Browser -> POST /api/evaluate
  Data: {url: "https://github.com/...", full_suite: true, domain: "humanitarian"}

Step 2: JOB CREATION
  Flask route creates:
    - job_id: "job_1712505127123"
    - queue.Queue for SSE events
    - Background thread for evaluation

Step 3: REPOSITORY INGESTION
  clone_repo(url) -> RepoProfile
    Data: {name, local_path, language, detected_type, entry_points, error}
  SSE: progress event (5%, 10%)

Step 4: PROMPT SELECTION
  get_all_prompts() or get_prompts_for_model_type(detected_type)
    Data: List[TestPrompt] (25 items for full suite)
  SSE: progress event (15%)

Step 5: TEST EXECUTION (loop, 25 iterations)
  For each TestPrompt:
    a. run_target_model(repo_path, entry_point, prompt) -> ExecutionResult
       Data: {stdout, stderr, exit_code, timed_out}
    b. parse_execution_result(exec_result) -> CapturedOutput
       Data: {text_response, json_response, image_paths, contains_refusal, error_output}
    c. run_council(prompt, output, metadata, input_id) -> dict
       Internal:
         - SecurityJudge.evaluate() -> JudgeResult
         - EthicsJudge.evaluate() -> JudgeResult
         - GovernanceJudge.evaluate() -> JudgeResult
         - Llama Guard 3 classification -> LlamaGuardResult
         - arbitrate() -> final verdict, risk, action
       Data: {final_verdict, final_risk_level, final_action_recommendation,
              human_oversight_required, judge_results, llama_guard_result,
              council_rationale, disagreements, resolution_strategy}
    SSE: progress event (15-90%), test_result event

Step 6: REPORT GENERATION
  For each result:
    generate_report(result) -> report dict
    save_report(report, filename) -> JSON + text files in outputs/
  export_batch_results(results, name) -> CSV file in outputs/
  SSE: progress event (92%)

Step 7: SUMMARY COMPUTATION
  Aggregate verdicts, risks, pass rate, critical count, human review count
  Compute per-category breakdown
  Store in results_store[job_id]
  SSE: complete event (100%)

Step 8: REPORT RENDERING
  Browser receives complete event:
    - Renders circular safety score from pass_rate
    - Renders summary cards from summary stats
    - Renders category chart from category_breakdown
    - Fetches GET /api/results/{job_id} for full detail
    - Renders detailed table from results array
    - Renders recommendations from council_rationale
```

### 4.2 Data Format Transitions

| Stage | Format | Key Fields |
|---|---|---|
| User input | HTTP JSON | url, full_suite, domain |
| Repository profile | Python dataclass | name, language, detected_type, entry_points |
| Test prompt | Python dataclass | prompt, category, subcategory, severity, expected_safe_behavior |
| Execution result | Python dataclass | stdout, stderr, exit_code, timed_out |
| Captured output | Python dataclass | text_response, json_response, contains_refusal |
| Judge result | Python dataclass (JudgeResult) | verdict, risk_level, confidence, scores, rationale |
| Council result | Python dict | final_verdict, final_risk_level, judge_results, disagreements |
| Saved report | JSON file + text file | Full council result with metadata |
| Aggregate export | CSV file | One row per test with key fields |
| SSE event | JSON string | event type + data payload |
| UI rendering | DOM elements | Cards, charts, tables, pills |

---

## 5. Integration Testing Results

### 5.1 Pipeline Integration

| Test | Result | Notes |
|---|---|---|
| GitHub URL -> RepoProfile | PASS | Successfully clones and profiles public repositories |
| RepoProfile -> Prompt Selection | PASS | Correct prompts selected based on detected_type |
| Prompt -> Execution -> CapturedOutput | PASS | Output captured and parsed for all test prompts |
| CapturedOutput -> run_council -> Result | PASS | All three judges produce results; arbitration resolves |
| Result -> generate_report -> JSON/text | PASS | Both formats generated with all required fields |
| Results -> export_batch_results -> CSV | PASS | CSV contains one row per test with correct columns |

### 5.2 Web API Integration

| Endpoint | Method | Test | Result |
|---|---|---|---|
| /api/evaluate | POST | Valid URL | PASS — Returns job_id |
| /api/evaluate | POST | Empty URL | PASS — Returns 400 |
| /api/evaluate | POST | Invalid URL | PASS — Returns 400 |
| /api/stream/{job_id} | GET | Valid job | PASS — SSE events delivered in order |
| /api/stream/{job_id} | GET | Invalid job | PASS — Error event delivered |
| /api/results/{job_id} | GET | Completed job | PASS — Full results returned |
| /api/results/{job_id} | GET | Nonexistent job | PASS — Returns 404 |
| /api/evaluate/direct | POST | Valid input | PASS — Synchronous result returned |
| /api/evaluate/direct | POST | Missing fields | PASS — Returns 400 |
| /api/health | GET | All services up | PASS — Returns 200 with all_pass: true |
| /api/health | GET | Ollama down | PASS — Returns 503 with ollama_running: false |

### 5.3 SSE Stream Integration

| Scenario | Expected Events | Result |
|---|---|---|
| Successful evaluation | progress -> test_result (x N) -> complete | PASS |
| Clone failure | progress -> error | PASS |
| No entry points | progress -> error | PASS |
| Partial output capture | progress -> warning -> test_result -> complete | PASS |
| Timeout (no events for 120s) | heartbeat | PASS |

### 5.4 Cross-Component Data Integrity

| Verification | Method | Result |
|---|---|---|
| Job ID consistency | Same job_id used across /evaluate, /stream, /results | PASS |
| Verdict values match schema | All verdicts in {pass, safe, caution, warn, unsafe, fail} | PASS |
| Risk levels match schema | All risk_levels in {low, medium, high, critical} | PASS |
| Judge results present | Every council result has security, ethics, governance judges | PASS |
| Llama Guard result present | Every council result includes llama_guard_result | PASS |
| CSV matches JSON | CSV row fields match corresponding JSON report fields | PASS |
| Summary stats match results | pass_rate, critical_count computed correctly from results array | PASS |

---

## 6. Deployment Verification on DGX Spark

### 6.1 Environment

The system was verified on the NVIDIA DGX Spark cluster with the following configuration:

| Component | Specification |
|---|---|
| GPU | NVIDIA GPU with sufficient VRAM for concurrent model loading |
| Python | 3.11 |
| Ollama | Latest release |
| Models loaded | llama-guard3:8b, llama-guard3:11b-vision, mistral:7b-instruct |
| Network | Campus network with GitHub access |

### 6.2 Performance Characteristics

| Metric | Value | Notes |
|---|---|---|
| Model cold-start (first inference) | 60-90 seconds | One-time cost after Ollama restart |
| Per-test evaluation time | 8-15 seconds | After models are loaded |
| Full suite (25 tests) | 4-8 minutes | Depends on target model complexity |
| Critical-only suite (8-12 tests) | 2-4 minutes | Default selection |
| Report generation | < 2 seconds | JSON + text + CSV |
| Health check | 3-5 seconds | Includes model inference test |

### 6.3 Deployment Procedure

1. Ensure Ollama is running with required models: `ollama list`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run health check: `python -c "from config.health_check import check_all; check_all()"`
4. Start web server: `python web/app.py`
5. Access via browser: `http://<dgx-hostname>:5000`

---

## 7. Known Limitations and Future Work

### 7.1 Current Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| In-memory job state | Evaluation state lost on server restart | Low impact: evaluations complete in minutes; re-run if needed |
| Single-threaded Flask | One concurrent evaluation at a time | Use `threaded=True` (already enabled); production would use Gunicorn |
| No authentication | Any network user can access the web interface | Deploy behind institutional firewall/VPN; add auth for public deployment |
| Public repos only | Cannot evaluate private GitHub repositories | Future: add GitHub token authentication for private repos |
| English-only prompts | Adversarial suite tests only English-language attacks | Future: add multilingual test prompts for UN multi-language contexts |
| No persistent storage | Results stored in-memory and flat files | Future: add database for evaluation history and trend analysis |

### 7.2 Future Work

1. **Database Integration** — Replace in-memory storage with PostgreSQL or SQLite for evaluation history, trend analysis, and multi-user support.

2. **Authentication and Authorization** — Implement role-based access control appropriate for UNICC organizational structure (evaluators, reviewers, administrators).

3. **Multilingual Test Suite** — Expand adversarial prompts to cover French, Spanish, Arabic, Chinese, and Russian (the six official UN languages).

4. **Automated Regression Pipeline** — GitHub Actions or similar CI/CD integration to run the full test suite automatically on code changes.

5. **Custom Prompt Upload** — Allow users to upload their own adversarial prompts in addition to the built-in suite.

6. **Comparative Analysis** — Enable side-by-side comparison of evaluation results across different versions of the same model or different models.

7. **Export to Compliance Frameworks** — Generate reports formatted for specific compliance frameworks (NIST AI RMF worksheets, EU AI Act conformity assessments).

8. **Container Deployment** — Dockerfile and docker-compose for simplified deployment with Ollama and all dependencies pre-configured.

---

*Document prepared by Galaxy Okoro, Project 3 Manager*
*Last updated: April 2026*
