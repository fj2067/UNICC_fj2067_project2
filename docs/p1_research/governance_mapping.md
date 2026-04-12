# Governance Framework Mapping

**UNICC AI Safety Lab -- Project 1**

| Field | Detail |
|---|---|
| **Author** | Coreece Lopez |
| **Course** | NYU MASY GC-4100 -- Spring 2026 |
| **Date** | March 16, 2026 |
| **Last Updated** | April 7, 2026 |
| **Client** | United Nations International Computing Centre (UNICC) |
| **Version** | 2.0 |

---

## 1. Purpose

This document maps the UNICC AI Safety Lab evaluation system to six international governance and security frameworks. The mapping demonstrates that the system's three-judge council architecture, Llama Guard safety layer, and infrastructure design collectively satisfy requirements from security, ethical, and regulatory perspectives.

Per the project memorandum, OWASP Top 10 for LLM Applications and MITRE ATT&CK are mandatory frameworks. Four additional frameworks are mapped to demonstrate comprehensive governance alignment suitable for a United Nations operational context.

### Frameworks Covered

1. OWASP Top 10 for LLM Applications (2025) -- **Mandatory**
2. MITRE ATT&CK Framework -- **Mandatory**
3. EU AI Act (2024)
4. NIST AI Risk Management Framework (2023)
5. ISO/IEC 42001:2023 -- AI Management System
6. UNESCO Recommendation on the Ethics of Artificial Intelligence

---

## 2. System Architecture Summary

The AI Safety Lab employs a **council-of-experts** evaluation architecture:

- **Llama Guard 3 8B** -- First-pass text safety classification (13 harm categories)
- **Llama Guard 3 Vision 11B** -- Image/multimodal safety classification
- **Mistral 7B Instruct v0.3** -- Reasoning engine for three specialized judges
- **Three-Judge Council**:
  - **Security Judge** -- Adversarial attacks, prompt injection, code safety, PII leakage
  - **Ethics Judge** -- Bias, fairness, transparency, manipulation, hallucination
  - **Governance Judge** -- Policy compliance, regulatory alignment, autonomous action, transparency readiness
- **Arbitration Engine** -- Strictest-wins aggregation with disagreement tracking
- **Infrastructure** -- NYU DGX Spark cluster, sandbox isolation, 300-second timeout

---

## 3. OWASP Top 10 for LLM Applications (2025) -- Mandatory

The OWASP Top 10 for LLM Applications identifies the most critical security risks in large language model deployments. Every risk category is addressed by one or more system components.

| OWASP ID | Risk Name | System Component(s) | Detection / Mitigation Logic | Coverage Level |
|---|---|---|---|---|
| **LLM01** | Prompt Injection | Security Judge | Direct injection detection via pattern matching for override commands ("ignore previous instructions," "you are now," "system prompt:"). Indirect injection detection via persona adoption triggers ("act as," "roleplay as," "pretend you are"). System prompt leakage detection for extraction attempts targeting internal configuration. Multi-pattern adversarial battery with 10+ injection variants tested per evaluation. | **Full** |
| **LLM02** | Insecure Output Handling | All Three Judges + Llama Guard | Llama Guard 3 performs first-pass content safety classification across 13 harm categories. Security Judge screens outputs for executable code fragments, script injection, and markup injection. Ethics Judge evaluates output for manipulative framing, deceptive content, and hallucinated information. Governance Judge checks output against organizational policy boundaries and transparency requirements. | **Full** |
| **LLM03** | Training Data Poisoning | Input Layer | Agent lineage documentation required before evaluation begins. Model provenance tracking (open-weight models with documented training data and version history). Evaluation metadata records model name, version, and source for audit trail. System does not fine-tune models, reducing poisoning attack surface. | **Partial** (detection-focused; system evaluates agents, not training pipelines) |
| **LLM04** | Model Denial of Service | Infrastructure | DGX Spark partition isolation prevents resource contention across evaluation jobs. Sandbox timeout enforced at 300 seconds -- any evaluation exceeding this limit is terminated. Ollama connection timeout at 180 seconds with maximum 2 retries. Cold-start detection with exponential backoff (first inference 30--90 seconds). GPU memory monitoring (17 GB of 128 GB allocated, leaving substantial headroom). | **Full** |
| **LLM05** | Supply Chain Vulnerabilities | Deployment Configuration | Exclusive use of open-weight models with publicly auditable architectures (Llama Guard 3, Mistral 7B). All model versions pinned and documented in deployment configuration. Ollama serves as a single, auditable inference gateway. No third-party plugins or opaque API dependencies in the evaluation pipeline. Anthropic API used only as a documented fallback with explicit API key management per Dr. Fortino's requirements. | **Full** |
| **LLM06** | Sensitive Information Disclosure | Governance Judge + Security Judge | PII detection via compiled regular expressions for: Social Security Numbers (XXX-XX-XXXX), credit card numbers (13--19 digit patterns), email addresses, phone numbers (international formats), passport numbers, IP addresses (IPv4), dates of birth (multiple formats). Security Judge flags any PII detected in agent outputs. Governance Judge assesses whether disclosure violates organizational data handling policies. Evidence arrays capture exact matches for audit review. | **Full** |
| **LLM07** | Insecure Plugin Design | Security Judge | Code safety analysis detects dangerous function calls: `eval()`, `exec()`, `os.system()`, `subprocess.run()`, `subprocess.Popen()`, `subprocess.call()`. File system access detection for `open()` with write modes, `os.remove()`, `shutil.rmtree()`. Network access detection for `requests.get/post`, `urllib`, `socket` operations. Import analysis for dangerous modules (`pickle`, `marshal`, `ctypes`). Each detection generates a flag with severity rating and evidence. | **Full** |
| **LLM08** | Excessive Agency | Governance Judge | Autonomous action detection: monitors for self-directed decision-making without human authorization. Tool use detection: flags agents that invoke external tools, APIs, or system commands. Code execution detection: identifies agents that generate and run code autonomously. External API call detection: flags outbound network requests to third-party services. Escalation scoring: actions requiring human oversight trigger `human_oversight_required: true` in council output. | **Full** |
| **LLM09** | Overreliance | Ethics Judge + Governance Judge | Ethics Judge evaluates transparency: does the agent acknowledge uncertainty, limitations, and confidence levels? Analytical context detection: does the agent provide sourcing, caveats, and alternative perspectives? Hallucination detection: cross-references claims against prompt context for unsupported assertions. Governance Judge transparency readiness scoring: rates agent's suitability for deployment where users may over-trust outputs. Combined scoring produces a transparency dimension visible in final results. | **Full** |
| **LLM10** | Model Theft | Infrastructure | NYU DGX Spark access control: authentication required via SPS Sandbox portal. Partition isolation: evaluation jobs run in dedicated GPU partitions. No external network access permitted within sandbox environment. Model weights stored locally on cluster -- not exposed to public endpoints. API keys managed through environment variables, never hardcoded or logged. `.gitignore` excludes `.env` files from version control. | **Full** |

### OWASP Coverage Summary

| Coverage Level | Count | Percentage |
|---|---|---|
| Full | 9 | 90% |
| Partial | 1 | 10% |
| None | 0 | 0% |

**Note on LLM03 (Training Data Poisoning):** The system evaluates AI agents, not their training pipelines. Coverage is partial by design -- the system documents agent lineage and provenance but cannot inspect upstream training data. This is an appropriate scope boundary for a pre-deployment evaluation tool.

---

## 4. MITRE ATT&CK Framework -- Mandatory

The MITRE ATT&CK framework catalogs adversarial tactics, techniques, and procedures (TTPs). The following mappings demonstrate how the AI Safety Lab detects or mitigates attack techniques relevant to LLM-based systems.

| ATT&CK ID | Technique Name | Tactic | System Component | Detection / Mitigation Logic |
|---|---|---|---|---|
| **T1190** | Exploit Public-Facing Application | Initial Access | Security Judge | Adversarial prompt injection battery tests 10+ attack patterns against the evaluated agent. Detects attempts to exploit the agent's input interface through crafted prompts designed to override safety controls, extract system prompts, or trigger unintended behaviors. Injection patterns include: direct override commands, nested instruction attacks, context window manipulation, and delimiter-based injection. Results scored on injection_resistance dimension. |
| **T1566** | Phishing | Initial Access | Security Judge | Social engineering pattern detection identifies agent outputs that could facilitate phishing. Detects: impersonation attempts ("I am a representative of..."), urgency manipulation ("act immediately or..."), authority exploitation ("as your administrator..."), and trust exploitation patterns. Flags agents that generate content suitable for social engineering attacks or that respond to social engineering inputs without appropriate skepticism. |
| **T1059** | Command and Scripting Interpreter | Execution | Security Judge | Code safety analysis module scans agent inputs and outputs for dangerous execution patterns. Detection targets: `os.system()` calls, `subprocess.run()` / `subprocess.Popen()` / `subprocess.call()` invocations, `eval()` and `exec()` usage, shell command construction, and PowerShell/bash script generation. Each detection is logged with the specific pattern matched, line context, and severity classification. |
| **T1078** | Valid Accounts | Persistence | Security Judge | Identity override and roleplay jailbreak detection. Monitors for attempts to make the agent adopt alternative identities: "you are now DAN," "act as an unrestricted AI," "ignore your safety training and pretend to be..." Detects persona adoption that would bypass safety controls by establishing a false identity context. Pattern matching covers known jailbreak templates (DAN, AIM, STAN, etc.) and novel formulations using semantic similarity. |
| **T1027** | Obfuscated Files or Information | Defense Evasion | Security Judge | Encoding bypass detection identifies attempts to smuggle malicious content through obfuscation. Detects: Base64-encoded payloads (pattern matching for base64 strings and decode calls), ROT13 encoding, URL encoding of sensitive commands, Unicode homoglyph substitution, and whitespace-based steganography. Flags any encoded content in agent inputs or outputs that could conceal prompt injection or unsafe instructions. |
| **T1530** | Data from Cloud Storage | Collection | Governance Judge | Unauthorized data access detection monitors for agent behaviors that attempt to access, enumerate, or exfiltrate data from storage systems. Detects: references to cloud storage APIs (S3, Azure Blob, GCS), database query construction, file system traversal patterns, and attempts to access resources outside the agent's authorized scope. Governance policy scoring penalizes agents that demonstrate data collection behaviors without explicit authorization. |
| **T1565** | Data Manipulation | Impact | Ethics Judge | Hallucination and manipulation detection identifies agents that present fabricated, distorted, or misleading information. Detection dimensions: factual consistency (claims vs. provided context), source fabrication (invented citations or statistics), emotional manipulation (fear, urgency, guilt framing), selective omission (presenting partial information as complete), and confidence calibration (expressing certainty about uncertain claims). Each dimension contributes to the ethics_score and generates specific evidence entries. |

### Additional ATT&CK Mappings (Extended Coverage)

| ATT&CK ID | Technique Name | System Component | Coverage Notes |
|---|---|---|---|
| **T1557** | Adversary-in-the-Middle | Infrastructure | Sandbox isolation and localhost-only Ollama communication prevent MITM attacks on the inference pipeline. |
| **T1499** | Endpoint Denial of Service | Infrastructure | Timeout enforcement (300s sandbox, 180s Ollama) and retry limits (max 2) prevent resource exhaustion. |
| **T1552** | Unsecured Credentials | Deployment Config | API keys stored in environment variables, `.env` excluded from version control, no hardcoded credentials in source. |

---

## 5. EU AI Act (2024)

The EU AI Act establishes a risk-based regulatory framework for AI systems deployed within or affecting the European Union. As UNICC serves EU member state organizations, alignment with this regulation is operationally relevant.

### Article 5 -- Prohibited AI Practices

| Prohibited Practice | System Alignment |
|---|---|
| Subliminal manipulation | Ethics Judge detects manipulative framing, emotional exploitation, and deceptive persuasion techniques in agent outputs. Agents exhibiting these behaviors receive "unsafe" or "fail" verdicts. |
| Exploitation of vulnerabilities | Ethics Judge fairness dimension evaluates whether agent outputs exploit age, disability, or socioeconomic vulnerabilities. Governance Judge assesses population-level impact. |
| Social scoring | Governance Judge policy compliance module flags agents that implement or facilitate social scoring systems. Detected via pattern matching for scoring/ranking of individuals based on social behavior. |
| Real-time biometric identification | Out of scope (system evaluates text/image-based AI agents, not biometric systems). Noted as a boundary condition in evaluation reports. |

### Articles 9--15 -- High-Risk AI System Requirements

| Article | Requirement | System Implementation |
|---|---|---|
| Art. 9 | Risk management system | Three-judge council implements continuous risk assessment across security, ethics, and governance dimensions. Risk levels (low/medium/high/critical) with defined thresholds (critical >= 0.85, high >= 0.65, medium >= 0.40). |
| Art. 10 | Data and data governance | Agent lineage documentation captures training data provenance. Evaluation logs (JSONL format) maintain complete audit trails of all assessments. |
| Art. 11 | Technical documentation | Full system documentation maintained: architecture blueprints, deployment configuration, governance mappings, integration specifications, and literature survey. |
| Art. 12 | Record-keeping | Every evaluation produces structured JSONL logs with timestamps, model versions, scores, rationale, evidence, and verdicts. Logs are append-only and support temporal auditing. |
| Art. 13 | Transparency and provision of information | Governance Judge transparency readiness scoring. Ethics Judge transparency dimension. Council rationale provides human-readable explanation of every verdict. All scoring dimensions visible in output. |
| Art. 14 | Human oversight | `human_oversight_required` boolean in council output. Triggered by: critical risk level, judge disagreements, novel attack patterns, or governance policy violations. Designed as human-in-the-loop, not human-on-the-loop. |
| Art. 15 | Accuracy, robustness, and cybersecurity | Baseline validation (20/20 test cases passed). Security Judge adversarial battery tests robustness. Infrastructure isolation and timeout enforcement address cybersecurity. |

### Article 50 -- Transparency Obligations

| Obligation | System Implementation |
|---|---|
| AI-generated content disclosure | Governance Judge evaluates whether the assessed agent properly discloses its AI nature. Transparency readiness score reflects this. |
| Explanation of decision-making | Council output includes `council_rationale` (narrative explanation), per-judge `rationale` arrays, and `evidence` arrays linking conclusions to specific observations. |
| Notification of AI interaction | System metadata records that evaluation was performed by AI judges, maintaining transparency about the evaluation process itself. |

---

## 6. NIST AI Risk Management Framework (AI RMF 1.0, 2023)

The NIST AI RMF provides a voluntary framework organized around four core functions. The AI Safety Lab maps to all four.

### GOVERN Function -- Establish AI Risk Management Culture

| GOVERN Subcategory | System Implementation |
|---|---|
| GOVERN 1 -- Policies and procedures | Three-judge council architecture encodes organizational risk policies into automated evaluation. Governance Judge specifically enforces UNICC policy requirements. |
| GOVERN 2 -- Accountability structures | Each judge produces independently attributable results. Council arbitration provides clear decision trail. `human_oversight_required` flag establishes escalation accountability. |
| GOVERN 3 -- Workforce diversity and competence | Three-student project team with complementary expertise (research/architecture, engine development, testing/UX). Multi-judge design prevents single-perspective bias. |
| GOVERN 4 -- Organizational commitments | Governance mapping to six frameworks demonstrates organizational commitment to responsible AI. UNICC AI Hub alignment ensures institutional backing. |
| GOVERN 5 -- Processes for engagement | Stakeholder analysis covers IT developers, AI Hub, UN partner agencies, and management. System designed for integration into existing UNICC shared-services workflows. |

### MAP Function -- Identify and Contextualize AI Risks

| MAP Subcategory | System Implementation |
|---|---|
| MAP 1 -- Context and scope | Domain sensitivity detection: agents serving humanitarian, legal, medical, or financial contexts receive heightened scrutiny. |
| MAP 2 -- Risk categorization | Multi-dimensional risk scoring across security, ethics, and governance domains. Four risk levels with quantitative thresholds. |
| MAP 3 -- Benefits and costs | Situational analysis documents cost-benefit of automated pre-deployment evaluation vs. manual review or no review. |
| MAP 4 -- Risk identification | Security Judge maps OWASP/MITRE risks. Ethics Judge maps bias and manipulation risks. Governance Judge maps compliance risks. Comprehensive risk surface coverage. |
| MAP 5 -- Impact characterization | Capability risk assessment: agents with tool use, code execution, or external API access capabilities receive elevated risk scoring. Population-level impact considered by Governance Judge. |

### MEASURE Function -- Quantify AI Risks

| MEASURE Subcategory | System Implementation |
|---|---|
| MEASURE 1 -- Appropriate metrics | Multi-dimensional scoring: each judge produces domain-specific scores (e.g., injection_resistance, bias_score, policy_compliance) as floats between 0 and 1. |
| MEASURE 2 -- Evaluation methods | Llama Guard 3 provides categorical safety classification (13 harm categories). Mistral 7B provides nuanced reasoning-based evaluation. Dual-method approach reduces blind spots. |
| MEASURE 3 -- Tracking over time | JSONL logging with timestamps enables temporal trend analysis. Baseline validation (20/20 passed) establishes measurement benchmark. |
| MEASURE 4 -- Feedback integration | Disagreement tracking between judges surfaces measurement uncertainty. Council rationale explains how conflicting signals were resolved. |

### MANAGE Function -- Prioritize and Act on AI Risks

| MANAGE Subcategory | System Implementation |
|---|---|
| MANAGE 1 -- Risk prioritization | Strictest-wins arbitration ensures highest-detected risk drives final verdict. Critical risks automatically require human oversight. |
| MANAGE 2 -- Risk response | Six-level verdict scale (pass/safe/caution/warn/unsafe/fail) with mapped actions: deploy, deploy with monitoring, deploy with restrictions, review required, block deployment, block and investigate. |
| MANAGE 3 -- Risk monitoring | Continuous evaluation capability via API endpoints. Streaming results via SSE for real-time monitoring. |
| MANAGE 4 -- Risk communication | Structured output schema provides machine-readable results for automated pipelines and human-readable rationale for decision-makers. |

---

## 7. ISO/IEC 42001:2023 -- AI Management System

ISO/IEC 42001 specifies requirements for establishing, implementing, maintaining, and continually improving an AI management system (AIMS).

| ISO/IEC 42001 Clause | Requirement Area | System Implementation |
|---|---|---|
| **4 -- Context of the organization** | Understanding the organization and its context | Situational analysis documents UNICC's operating environment, stakeholder needs, and the intergovernmental context driving AI safety requirements. |
| **5 -- Leadership** | Leadership commitment and AI policy | Project structure under NYU MASY GC-4100 with faculty oversight (Dr. Fortino). UNICC AI Hub provides institutional leadership context. Governance Judge enforces policy-level requirements. |
| **6 -- Planning** | Risk assessment and treatment | Three-judge architecture implements structured risk assessment. Risk thresholds (critical >= 0.85, high >= 0.65, medium >= 0.40) define treatment boundaries. Governance mapping to six frameworks demonstrates planning rigor. |
| **7 -- Support** | Resources, competence, documentation | DGX Spark cluster (128 GB GPU, 2-node NVIDIA) provides infrastructure resources. Three-student team with defined competency areas. Full documentation suite: architecture blueprint, governance mapping, integration spec, deployment config, literature survey. |
| **8 -- Operation** | Operational planning and control | Defined evaluation pipeline: input validation, Llama Guard classification, three-judge assessment, council arbitration, verdict output. API endpoints provide standardized operational interfaces. Timeout and retry logic ensure operational resilience. |
| **9 -- Performance evaluation** | Monitoring, measurement, analysis | Baseline validation (20/20 test cases, 100% pass rate). JSONL logging for audit and trend analysis. Multi-dimensional scoring provides granular performance data. Disagreement tracking between judges measures internal consistency. |
| **10 -- Improvement** | Nonconformity, corrective action, continual improvement | Modular architecture supports iterative improvement (judges can be updated independently). Version tracking in output schema (version 2.0). Literature survey integration ensures system evolves with research advances. Project sequence (P1 -> P2 -> P3) demonstrates structured improvement methodology. |

### Annex A -- AI-Specific Controls

| Control | Implementation |
|---|---|
| A.2 -- AI impact assessment | Ethics Judge bias and fairness evaluation. Governance Judge population impact assessment. |
| A.3 -- AI system lifecycle | Evaluation occurs at the pre-deployment gate. System designed to support re-evaluation at any lifecycle stage. |
| A.4 -- Data management | Agent lineage documentation. Evaluation data logged in structured JSONL format. PII detection prevents sensitive data leakage. |
| A.5 -- AI transparency | Council rationale, per-judge rationale arrays, evidence arrays, and transparency readiness scoring. |
| A.6 -- Accountability | Traceable verdicts with judge-level attribution. Human oversight triggers for high-risk determinations. |

---

## 8. UNESCO Recommendation on the Ethics of Artificial Intelligence (2021)

The UNESCO Recommendation establishes global ethical principles for AI. As a UN-system organization, UNICC has direct alignment obligations.

### Principle 1: Proportionality and Do No Harm

| Dimension | System Implementation |
|---|---|
| Proportionality | Risk-proportionate evaluation: four risk levels with escalating response actions. Low-risk agents receive lighter-touch evaluation; critical-risk agents trigger mandatory human oversight and deployment blocking. |
| Do no harm | Ethics Judge evaluates agent outputs for potential harm across multiple dimensions: physical safety, psychological manipulation, misinformation, and discrimination. Security Judge prevents agents from causing harm through technical exploits. Llama Guard 3 classifies across 13 harm categories including violent crimes, sexual content, and self-harm. |
| Necessity | Governance Judge assesses whether agent capabilities are proportionate to their stated purpose. Excessive agency detection flags agents with capabilities beyond their operational requirements. |

### Principle 2: Fairness and Non-Discrimination

| Dimension | System Implementation |
|---|---|
| Fairness | Ethics Judge bias detection: evaluates agent outputs for demographic bias across protected categories (race, gender, age, religion, national origin, disability, sexual orientation). Scores bias_score dimension with evidence of detected disparities. |
| Non-discrimination | Multi-judge design reduces evaluation bias. Three independent perspectives (security, ethics, governance) prevent single-dimension discrimination in verdicts. Literature survey finding: LLM-as-judge exhibits position bias, verbosity bias, and self-enhancement bias (Zheng et al. 2023) -- multi-judge architecture specifically mitigates these. |
| Inclusion | System designed for UNICC's multilingual, multicultural stakeholder environment. Governance Judge policy compliance adapts to organizational context. |

### Principle 3: Privacy and Data Protection

| Dimension | System Implementation |
|---|---|
| PII detection | Security Judge and Governance Judge implement regex-based PII detection for: SSN (XXX-XX-XXXX), credit card numbers (13--19 digits), email addresses, phone numbers (international formats), passport numbers, IP addresses (IPv4), dates of birth (multiple date formats). |
| Data minimization | Evaluation logs capture only necessary assessment data. No agent training data is stored or retained by the evaluation system. |
| Access control | DGX Spark partition isolation. Environment variable-based credential management. `.env` file excluded from version control. |

### Principle 4: Transparency and Explainability

| Dimension | System Implementation |
|---|---|
| Transparency | Every verdict includes: council_rationale (narrative explanation), per-judge rationale arrays (itemized reasoning), evidence arrays (specific observations), and scoring breakdowns (numerical dimensions). |
| Explainability | Six-level verdict scale provides intuitive risk communication. Risk levels (low/medium/high/critical) map to actionable recommendations. Disagreement tracking surfaces evaluation uncertainty. |
| Auditability | JSONL logging with timestamps, model versions, and complete evaluation context. Append-only log format supports forensic analysis. Schema versioning (v2.0) tracks output format evolution. |

### Principle 5: Human Oversight and Determination

| Dimension | System Implementation |
|---|---|
| Human-in-the-loop | `human_oversight_required` boolean triggered by: critical risk determinations, inter-judge disagreements, novel threat patterns, and policy ambiguity. System recommends, humans decide. |
| Right to appeal | Structured output format enables human reviewers to examine evidence, rationale, and scoring at any granularity level. Disagreement arrays highlight where judges differed, giving reviewers clear entry points for re-evaluation. |
| Ultimate human authority | System produces advisory verdicts, not enforcement actions. Deployment decisions remain with UNICC stakeholders. Action recommendations range from "deploy" to "block and investigate" but are recommendations only. |

---

## 9. Cross-Framework Alignment Matrix

This matrix shows how system components serve multiple frameworks simultaneously.

| System Component | OWASP | MITRE | EU AI Act | NIST RMF | ISO 42001 | UNESCO |
|---|---|---|---|---|---|---|
| **Security Judge** | LLM01, LLM02, LLM05, LLM06, LLM07 | T1190, T1566, T1059, T1078, T1027 | Art. 15 | MEASURE 1-2 | Clause 8, A.4 | Principle 1 |
| **Ethics Judge** | LLM02, LLM09 | T1565 | Art. 5, Art. 50 | MAP 4 | A.2 | Principles 1, 2, 4 |
| **Governance Judge** | LLM06, LLM08, LLM09 | T1530 | Art. 9, 13, 14 | GOVERN 1-2, MANAGE 2 | Clause 5, 6, A.5, A.6 | Principles 3, 5 |
| **Llama Guard 3** | LLM02 | -- | Art. 9 | MEASURE 2 | Clause 8 | Principle 1 |
| **Council Arbitration** | -- | -- | Art. 14 | MANAGE 1 | Clause 9 | Principle 5 |
| **Infrastructure (DGX)** | LLM04, LLM10 | T1557, T1499, T1552 | Art. 15 | MANAGE 3 | Clause 7 | Principle 3 |
| **JSONL Logging** | -- | -- | Art. 12 | MEASURE 3 | Clause 9 | Principle 4 |
| **Human Oversight Flag** | -- | -- | Art. 14 | MANAGE 4 | A.6 | Principle 5 |

---

## 10. Conclusion

The UNICC AI Safety Lab evaluation system achieves comprehensive alignment with six international governance frameworks. Key findings:

1. **OWASP coverage: 90% full, 10% partial.** All 10 LLM application risks are addressed. The single partial coverage (LLM03 -- Training Data Poisoning) reflects an appropriate scope boundary: the system evaluates agents, not their training pipelines.

2. **MITRE ATT&CK coverage: 10 techniques mapped.** Seven primary and three extended technique mappings demonstrate the Security Judge's adversarial detection capabilities.

3. **EU AI Act alignment: all applicable articles addressed.** The system supports high-risk AI requirements (Articles 9--15), transparency obligations (Article 50), and prohibited practice detection (Article 5).

4. **NIST AI RMF: all four functions covered.** GOVERN, MAP, MEASURE, and MANAGE functions are implemented across the system architecture.

5. **ISO/IEC 42001: all clauses addressed.** Documentation, risk assessment, operational controls, performance evaluation, and improvement processes are in place.

6. **UNESCO Ethics: all five principles implemented.** Proportionality, fairness, privacy, transparency, and human oversight are embedded in the system design.

This mapping supports the assessment that the AI Safety Lab is suitable for pre-deployment evaluation of AI agents within the UNICC ecosystem and the broader UN system.

---

*Document prepared by Coreece Lopez for NYU MASY GC-4100 (Spring 2026). UNICC AI Safety Lab -- Project 1.*
