# AI Safety Lab — System Architecture

## Document Control

| Field | Value |
|-------|-------|
| Version | 2.0 |
| Date | April 2026 |
| Project | UNICC AI Safety Lab — Spring 2026 Capstone |
| Author | Team [Your Team Name] |
| Status | Implementation / Proof of Concept |

---

## 1. System Overview

The UNICC AI Safety Evaluation Lab is a multi-module inference ensemble deployed
on a standalone Small Language Model (SLM) platform. It evaluates AI agents for
trust, safety, and governance compliance before production deployment within the
UNICC AI Sandbox.

### Core Principle
Three independent expert modules (judges) provide diverse safety assessments.
Their outputs are synthesized through an orchestration layer that applies a
conservative (strictest-wins) arbitration strategy aligned with the precautionary
principle appropriate for UN institutional contexts.

---

## 2. Architecture Diagram

```
                    +------------------------------------------+
                    |          Web Interface (Project 3)        |
                    |    Flask + SSE + Turnitin-style Reports   |
                    +------------------------------------------+
                                       |
                                  REST API / Python API
                                       |
                    +------------------------------------------+
                    |         API Layer  (api.py)               |
                    |  evaluate_agent() / evaluate_repo()       |
                    +------------------------------------------+
                                       |
               +-----------------------------------------------+
               |          Council Orchestrator                  |
               |     orchestrator.py + arbitration.py           |
               |  Synthesis | Disagreement Detection | Voting  |
               +-----------------------------------------------+
                    /              |              \
          +------------+   +------------+   +---------------+
          | Security   |   | Ethics     |   | Governance    |
          | Judge      |   | Judge      |   | Judge         |
          | (Module 1) |   | (Module 2) |   | (Module 3)    |
          +------------+   +------------+   +---------------+
            S1,S2,S7,       S3,S4,S6,       S5,S8,S13
            S9,S14          S10,S11,S12     + Deployment
            + PII Regex     + Group Det.    + Readiness
                    \              |              /
               +-----------------------------------------------+
               |       Llama Guard 3 (8B) — Text Safety        |
               |       Llama Guard 3 Vision (11B) — Images     |
               +-----------------------------------------------+
                                       |
                              Ollama Local Endpoint
                           (DGX Spark Cluster / Local)
                                       |
               +-----------------------------------------------+
               |         GitHub Ingestion Pipeline             |
               |  Clone -> Profile -> Sandbox -> Capture       |
               +-----------------------------------------------+
                                       |
               +-----------------------------------------------+
               |     Target AI Projects (Fall 24 / Spr 25)     |
               |        GitHub Repository URLs                 |
               +-----------------------------------------------+
```

---

## 3. Module Decomposition

### 3.1 Ingestion Layer
- **github_loader.py**: Clones repos, detects language/framework, identifies
  entry points, profiles project type (chatbot, RAG, agent, content_gen)
- **sandbox_runner.py**: Executes target models in restricted subprocess or
  Docker container. No network, limited memory, timeout enforcement.
- **output_capture.py**: Parses stdout/stderr/files into structured
  CapturedOutput objects. Detects refusals, extracts JSON, collects images.

### 3.2 Test Generation
- **adversarial_prompts.py**: 25+ test prompts across 6 categories:
  prompt injection, harmful content, PII leakage, hate/discrimination,
  governance, and safe baselines. Mapped to OWASP LLM Top 10 and MITRE ATT&CK.

### 3.3 Guardrails (Llama Guard 3)
- **llama_guard_text.py**: Invokes Meta Llama Guard 3 (8B) via Ollama.
  Classifies text against S1-S14 MLCommons hazard taxonomy. Includes retry
  logic for DGX cold-start reliability.
- **llama_guard_vision.py**: Invokes Llama Guard 3 Vision (11B) for image
  safety: obscene content, sensitive documents, PII in images, hateful imagery.

### 3.4 Expert Judge Modules (Council of Experts)
Each judge produces a standardized JudgeResult with multi-dimensional scores,
rationale, evidence, flags, and confidence levels.

| Judge | Dimensions | Llama Guard Categories |
|-------|-----------|----------------------|
| SecurityJudge | harmfulness, privacy, prompt_injection, legal_compliance, deception, code_safety | S1, S2, S7, S9, S14 |
| EthicsJudge | hate_hostility, discrimination, xenophobia, human_dignity, fairness, incitement, sexual_content | S3, S4, S6, S10, S11, S12 |
| GovernanceJudge | application_sensitivity, capability_risk, oversight_need, monitoring_readiness, transparency_readiness, deployment_readiness, compliance | S5, S8, S13 |

### 3.5 Council Orchestrator
- **orchestrator.py**: Coordinates independent judge evaluations, synthesizes
  final verdict using max-severity resolution, detects inter-judge disagreements.
- **arbitration.py**: Implements critique-and-synthesis mechanism. Identifies
  score-level disagreements, applies conservative resolution, documents rationale.

### 3.6 Reporting
- **safety_report.py**: Generates JSON and human-readable text reports.
- **csv_export.py**: Batch CSV export, requirements compliance matrix.

### 3.7 Web Interface (Project 3)
- **Flask application** with Server-Sent Events for real-time progress.
- Turnitin-style evaluation reports with score breakdowns, graphs, recommendations.

---

## 4. Data Flow

```
1. User submits GitHub URL via Web UI or CLI
2. github_loader clones repo, profiles structure
3. adversarial_prompts selects test suite for model type
4. For each test prompt:
   a. sandbox_runner executes target model with prompt via stdin
   b. output_capture parses stdout into text + images
   c. SecurityJudge evaluates (Llama Guard S1,S2,S7,S9,S14 + PII regex)
   d. EthicsJudge evaluates (Llama Guard S3,S4,S6,S10,S11,S12 + patterns)
   e. GovernanceJudge evaluates (Llama Guard S5,S8,S13 + readiness checks)
   f. If images exist: Llama Guard 3 Vision evaluates each
   g. Orchestrator synthesizes all results
5. Reports generated (JSON, text, CSV)
6. Web UI renders Turnitin-style report with real-time updates
```

---

## 5. Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| SLM Platform | Ollama on DGX Spark | Standalone, no external APIs (memo requirement) |
| Safety Classifier | Llama Guard 3 (8B) | Open-source Meta model, MLCommons taxonomy |
| Vision Classifier | Llama Guard 3 Vision (11B) | Multimodal safety for images |
| Reasoning SLM | Mistral 7B Instruct | Open-weights, fits DGX memory alongside Guard |
| Backend | Python 3.11 + Flask | Standard, minimal dependencies |
| Frontend | Vanilla HTML/CSS/JS | No build step, clean/minimal aesthetic |
| Isolation | subprocess / Docker | Sandboxed target model execution |
| Deployment | DGX Spark Cluster | On-prem NVIDIA hardware, GPU inference |

---

## 6. Security Architecture

- **Target model isolation**: Subprocess with no network, limited memory, timeout
- **No external API calls in production**: All inference via local Ollama
- **No API keys in sandbox environment**: Stripped from subprocess env
- **Audit trail**: Every evaluation logged with timestamp, judge scores, rationale
- **Input validation**: GitHub URLs validated before cloning
- **Docker option**: Stronger isolation with --network=none, --read-only, --memory=512m

---

## 7. Deployment Architecture (DGX Spark)

```
DGX Spark Node (Team Partition)
├── Ollama Server (port 11434)
│   ├── llama-guard3:8b          (~5 GB VRAM)
│   ├── llama-guard3:11b-vision  (~7 GB VRAM, optional)
│   └── mistral:7b-instruct     (~5 GB VRAM)
├── Python 3.11 Environment
│   └── UNICC_AI_Safety_Lab/
│       ├── Flask web server (port 5000)
│       ├── Evaluation engine
│       └── Output reports
└── Cloned target repos (ephemeral)
```

**GPU Memory Budget**: ~17 GB for all 3 models simultaneously.
DGX Spark nodes typically have 128 GB VRAM — sufficient with headroom.

If memory is tight, models are loaded/unloaded on demand by Ollama automatically.
