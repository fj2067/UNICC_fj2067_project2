# UNICC AI Safety Evaluation Lab

## NYU MASY GC-4100 Applied Project Capstone — Spring 2026

**Team:** Coreece Lopez (P1) · Feruza Jubaeva (P2) · Galaxy Okoro (P3)
**Sponsor:** Dr. Andres Fortino | **Client:** UNICC | **Liaison:** Joseph Papa

The UNICC AI Safety Evaluation Lab is an end-to-end system for evaluating AI agents before deployment in the UN ecosystem. It accepts a GitHub repository URL, clones the target project, analyzes its source code and runtime behavior, and evaluates it through a **council of three independent expert judges** — Security, Ethics, and Governance — each backed by Llama Guard 3 safety classification (with Anthropic Claude API fallback). The council synthesizes independent assessments into a final APPROVE / REVIEW / REJECT verdict with actionable recommendations aligned to OWASP, MITRE ATT&CK, and UN governance frameworks.

## Project Sequence

This repository integrates three capstone projects in dependency order:

- **P1 — Research and Platform Preparation** (Coreece Lopez): Foundational research on multi-module inference ensembles, small language models, and AI governance frameworks. Produced the Functional Requirements Specification, architecture design, governance mapping, and deployment configuration for the DGX Spark cluster.

- **P2 — Fine-Tuning the SLM and Building the Council of Experts** (Feruza Jubaeva): Core implementation of the three-judge council-of-experts architecture. Built the ingestion pipeline (GitHub cloning, sandboxed execution, static analysis fallback), Llama Guard 3 integration with Anthropic fallback, adversarial test generation, and report synthesis.

- **P3 — Testing, User Experience, and Integration** (Galaxy Okoro): System integration, comprehensive testing with adversarial prompts, Flask web interface for submitting agents and viewing reports, user documentation, and monitoring/logging design.

## Quick Start

```bash
pip install -r requirements.txt
python main.py --repo https://github.com/FlashCarrot/VeriMedia --full-suite
```

For the web interface:

```bash
python web/app.py
# Open http://localhost:5000
```

Set `ANTHROPIC_API_KEY` as an environment variable for Claude API fallback when Ollama is unavailable.

## Repository Structure

```
unicc-ai-safety-lab-final/
├── main.py                    (P2) CLI entry point — evaluate repos or text
├── api.py                     (P2) Programmatic Python API
├── requirements.txt                Combined dependencies
│
├── config/                    (P2) Central settings, health checks
├── council/                   (P2) Council-of-experts orchestrator + arbitration
├── guardrails/                (P2) Llama Guard 3 text + vision safety classifiers
├── ingestion/                 (P2) GitHub cloning, sandboxed execution, static analysis
├── judges/                    (P2) SecurityJudge, EthicsJudge, GovernanceJudge
├── reporting/                 (P2) Safety report generation + CSV export
├── test_generation/           (P2) Adversarial prompt library (25+ prompts)
├── web/                       (P3) Flask web interface with SSE progress streaming
│
├── tests/                     (P2+P3) Unit tests + test cases
├── requirements/              (P2) Llama Guard mapping + safety requirements CSVs
├── outputs/                   (P2) Pre-generated evaluation results (JSON + TXT)
│
├── schemas/                   (P1) Output schema definitions
├── scripts/                   (P1) Model testing scripts
├── logs/                      (P1) Sample test logs
│
└── docs/
    ├── p1_research/           (P1) FRS, architecture, governance mapping, literature survey
    ├── p2_implementation/     (P2) Architecture, functional requirements, deployment, implementation
    └── p3_testing/            (P3) Test plan, results analysis, user manual, UX docs
```

## Documentation

### P1 — Research and Platform (docs/p1_research/)
- `FRS.md` — Functional Requirements Specification
- `architecture.md` — System architecture design
- `deployment_config.md` — DGX Spark cluster deployment configuration
- `governance_mapping.md` — OWASP/MITRE framework alignment
- `integration_spec.md` — Module integration specification
- `literature_survey.md` — Multi-module inference ensemble research
- `situational_analysis.md` — Current state analysis

### P2 — Implementation (docs/p2_implementation/)
- `01_ARCHITECTURE.md` — Council-of-experts technical architecture
- `02_FUNCTIONAL_REQUIREMENTS.md` — Detailed functional requirements
- `03_DEPLOYMENT_GUIDE.md` — Step-by-step deployment on DGX Spark
- `04_IMPLEMENTATION_STEPS.md` — Implementation roadmap and decisions

### P3 — Testing and UX (docs/p3_testing/)
- `test_plan.md` — Comprehensive test strategy
- `test_results_analysis.md` — Evaluation results and analysis
- `integration_report.md` — System integration report
- `user_manual.md` — End-user guide
- `ux_documentation.md` — UX design documentation
- `monitoring_logging.md` — Monitoring and logging design

## DGX Sandbox

```
Runtime: Python
Setup:  pip install -r requirements.txt
Run:    python3 main.py --repo https://github.com/FlashCarrot/VeriMedia --full-suite
```

## Test Results

- 25 adversarial prompts tested across prompt injection, harmful content, PII leakage, hate/discrimination, and governance categories
- 100% detection accuracy
- 0 false positives, 0 false negatives
- Pre-generated evaluation outputs available in `outputs/`
