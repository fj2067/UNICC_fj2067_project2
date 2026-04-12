# Literature Survey -- AI Safety Evaluation for Institutional Deployment

**UNICC AI Safety Lab -- Project 1**

| Field | Detail |
|---|---|
| **Author** | Coreece Lopez (based on Feruza Jubaeva's research contribution) |
| **Course** | NYU MASY GC-4100 -- Spring 2026 |
| **Date** | March 16, 2026 |
| **Last Updated** | April 7, 2026 |
| **Version** | 2.0 |

---

## 1. Introduction

This document summarizes the literature review conducted to inform the design of the UNICC AI Safety Lab evaluation system. The full literature survey, jointly developed by the project team, examines the state of the art in AI safety evaluation, LLM security, governance frameworks, and institutional deployment requirements.

### Why This Review Was Necessary

The UNICC AI Safety Lab is not a research prototype; it is a system intended for operational use within the United Nations International Computing Centre. This institutional context imposes requirements that go beyond typical academic AI safety research:

1. **Governance alignment.** UNICC operates under multiple overlapping regulatory and ethical frameworks (EU AI Act, UNESCO Recommendations, NIST RMF, ISO/IEC 42001). The system must satisfy all of them simultaneously.

2. **Adversarial realism.** AI agents deployed in UN contexts face sophisticated threat actors. Evaluation must go beyond benchmark performance to include adversarial robustness testing informed by current threat intelligence (OWASP, MITRE ATT&CK).

3. **Evaluation methodology limitations.** Emerging research reveals significant biases in LLM-as-judge paradigms. The system design must account for and mitigate these biases to produce trustworthy evaluations.

4. **Accountability requirements.** Institutional deployment demands auditable, explainable, and reproducible evaluation processes. The literature review identified engineering patterns (and gaps) for meeting these requirements.

5. **Multi-stakeholder environment.** UNICC serves 50+ UN system organizations with diverse risk tolerances and operational domains. The evaluation system must be flexible enough to accommodate this diversity.

The literature review informed every major architectural decision in the AI Safety Lab, from the multi-judge council design to the specific detection capabilities of each judge module.

---

## 2. Key Findings

### 2.1 No Single Evaluation Method Is Sufficient

A consistent finding across the literature is that no single evaluation method adequately captures the full risk surface of modern AI systems.

- **Chang et al. (2024)** provide a comprehensive survey of LLM evaluation methods, demonstrating that benchmark-based evaluation, human evaluation, and automated evaluation each capture different (and incomplete) aspects of model behavior. Their taxonomy reveals systematic blind spots in every evaluation paradigm.

- **Zheng et al. (2023)** show that even state-of-the-art LLM judges agree with human evaluators only 80--85% of the time, and this agreement rate drops significantly for nuanced safety-relevant judgments.

- **Wang et al. (2024)** find that evaluation robustness varies dramatically across domains and task types. Methods that perform well on general benchmarks may fail on domain-specific safety assessments.

**Design implication:** The AI Safety Lab uses a multi-method approach: Llama Guard categorical classification (pattern-based), Mistral 7B reasoning-based evaluation (three specialized judges), and structured arbitration (rule-based aggregation). No single method is trusted in isolation.

### 2.2 LLM-as-Judge Biases

The LLM-as-judge paradigm, while powerful, exhibits systematic biases that can compromise evaluation reliability.

- **Zheng et al. (2023)** identify three primary biases in the MT-Bench and Chatbot Arena studies:
  - **Position bias:** LLM judges favor the response presented first (or second, depending on the model), regardless of quality.
  - **Verbosity bias:** Longer responses receive higher ratings, even when the additional length does not add substantive value.
  - **Self-enhancement bias:** LLM judges rate responses from their own model family more favorably than responses from other models.

- **Sharma et al. (2025)** extend these findings to safety-specific evaluations, demonstrating that safety judges can exhibit **anchoring bias** (over-weighting the first safety signal detected) and **severity calibration drift** (inconsistent severity ratings across evaluation sessions).

- **Zhu et al. (2024)** explore mitigation strategies including multi-judge panels, calibration prompts, and structured evaluation rubrics.

**Design implication:** The three-judge architecture directly mitigates LLM-as-judge biases. Each judge evaluates a distinct domain (security, ethics, governance) with domain-specific rubrics, reducing position and verbosity biases. The council arbitration layer applies rule-based aggregation (strictest-wins) rather than relying on any single judge's severity calibration.

### 2.3 Competitive Oversight and Multi-Judge Evaluation

Multi-perspective and adversarial evaluation paradigms produce stronger safety signals than single-evaluator approaches.

- **Kenton et al. (2024)** investigate competitive oversight mechanisms where multiple AI systems evaluate each other's outputs. Their key finding: disagreement between evaluators is itself a valuable safety signal, often indicating edge cases that single evaluators miss.

- **Cen & Alur (2024)** formalize the theory behind multi-agent evaluation, showing that diverse evaluator perspectives improve coverage of the risk surface, particularly for adversarial and novel attack patterns.

- **Perez et al. (2022)** demonstrate that red-teaming with multiple AI systems discovers safety failures that single-model evaluation and human review both miss. Their work informs the adversarial testing component of the Security Judge.

**Design implication:** The council-of-experts architecture implements competitive oversight. Three judges with distinct expertise produce independent assessments. The arbitration engine tracks disagreements explicitly, and disagreement triggers human oversight review. This design is a direct application of Kenton et al.'s finding that evaluator disagreement is a safety signal.

### 2.4 Accountability Gap in AI Safety Engineering

The literature reveals a significant gap between AI safety research and operational accountability requirements.

- **Lu et al. (2024)** survey responsible AI practices in industry and find that most organizations lack standardized engineering patterns for implementing safety evaluations. Safety is often treated as an afterthought rather than an architectural requirement.

- **Raji et al. (2020)** propose structured audit frameworks for AI systems but note that few organizations have the technical infrastructure to implement them. Their work on algorithmic auditing informs the JSONL logging and evidence-tracking features of the AI Safety Lab.

- **Jobin et al. (2019)** analyze 84 AI ethics guidelines globally and find significant convergence on principles (transparency, fairness, non-maleficence) but divergence on implementation mechanisms. This gap between principle and practice is precisely what the AI Safety Lab addresses.

- **Phiri (2025)** defines three critical properties for AI audit systems: **integrity** (tamper-evident records), **coverage** (comprehensive risk surface evaluation), and **temporal coherence** (consistent evaluation over time). The AI Safety Lab's JSONL logging, multi-framework governance mapping, and versioned output schema address all three.

**Design implication:** The AI Safety Lab is designed as an engineering system, not a research prototype. Every evaluation produces a complete audit trail: structured logs, per-judge evidence, council rationale, and versioned output schemas. This directly addresses the accountability gap identified by Lu et al. and Raji et al.

### 2.5 Threat Landscape for LLM-Based Systems

The threat landscape for LLM-based systems is rapidly evolving, requiring evaluation systems to be both comprehensive and adaptable.

- **OWASP (2025)** Top 10 for LLM Applications identifies the most critical security risks, including prompt injection (LLM01), insecure output handling (LLM02), and excessive agency (LLM08). These risks are not theoretical: they represent observed attack patterns in production LLM deployments.

- **Cisco (2026)** AI Security Report documents the accelerating sophistication of attacks against AI systems in enterprise environments. Key findings include: 78% of organizations are now using AI in some capacity, creating a massive attack surface; prompt injection attacks have evolved from simple override commands to multi-turn, context-aware manipulation; and supply chain attacks targeting model weights and training data are increasing.

- **MITRE** ATT&CK framework provides a structured taxonomy for adversarial techniques. While originally designed for traditional cybersecurity, its technique catalog (T1190, T1566, T1059, T1078, T1027, etc.) maps directly to LLM attack vectors, as demonstrated in the governance mapping document.

- **European Parliament (2024)** EU AI Act establishes regulatory requirements that create legal liability for organizations deploying unsafe AI systems. Non-compliance carries penalties of up to 35 million EUR or 7% of global revenue.

**Design implication:** The Security Judge implements detection logic mapped to both OWASP and MITRE frameworks. The adversarial test battery includes 10+ attack patterns covering prompt injection, jailbreak, persona adoption, encoding bypass, social engineering, and code execution attempts. The governance mapping document demonstrates compliance with six frameworks, including the mandatory OWASP and MITRE mappings.

### 2.6 Audit Requirements for AI Systems

Rigorous evaluation systems require audit capabilities that go beyond simple pass/fail logging.

- **Phiri (2025)** defines three essential properties of AI audit infrastructure:
  - **Integrity:** Audit records must be tamper-evident. The system must prevent or detect modification of historical evaluation results.
  - **Coverage:** Audits must address the complete risk surface, not just easily measurable dimensions.
  - **Temporal coherence:** Evaluations must produce consistent, comparable results over time, enabling trend analysis and regression detection.

- **Raji et al. (2020)** provide a practical framework for internal algorithmic auditing, emphasizing the importance of structured documentation, stakeholder engagement, and iterative evaluation.

- **NIST (2023)** AI Risk Management Framework formalizes four audit-relevant functions (GOVERN, MAP, MEASURE, MANAGE) that provide a structured approach to risk documentation and tracking.

**Design implication:** The AI Safety Lab addresses all three of Phiri's audit properties. Integrity: append-only JSONL logs with timestamps and version metadata. Coverage: three-judge council with multi-framework governance mapping ensures comprehensive risk surface evaluation. Temporal coherence: versioned output schema (v2.0), baseline validation (20/20 test suite), and structured scoring dimensions enable consistent comparison across evaluations.

---

## 3. Design Implications for the AI Safety Lab

The literature review directly shaped the following architectural decisions:

### 3.1 Multi-Judge Council Architecture

| Literature Finding | Design Decision |
|---|---|
| No single evaluation method is sufficient (Chang et al. 2024) | Three specialized judges (security, ethics, governance) plus Llama Guard categorical classification |
| LLM-as-judge biases compromise single-evaluator reliability (Zheng et al. 2023) | Independent domain-specific judges with structured rubrics; rule-based arbitration rather than LLM-based aggregation |
| Competitive oversight produces stronger signals (Kenton et al. 2024) | Disagreement tracking as a first-class feature; disagreement triggers human oversight |
| Multi-agent evaluation improves risk coverage (Cen & Alur 2024) | Three distinct evaluation perspectives ensure broader coverage of the risk surface |

### 3.2 Adversarial Security Testing

| Literature Finding | Design Decision |
|---|---|
| Prompt injection is the top LLM risk (OWASP 2025) | Security Judge implements multi-pattern injection detection battery |
| Attack sophistication is increasing (Cisco 2026) | Detection covers encoding bypass, persona adoption, multi-turn manipulation, and novel attack formulations |
| MITRE ATT&CK provides structured threat taxonomy | Security Judge detection logic mapped to specific ATT&CK techniques |
| Red-teaming with AI discovers failures missed by humans (Perez et al. 2022) | Adversarial test battery includes AI-generated attack prompts |

### 3.3 Governance and Accountability

| Literature Finding | Design Decision |
|---|---|
| Accountability gap between principles and practice (Lu et al. 2024, Jobin et al. 2019) | System produces complete audit trails with structured evidence and rationale |
| Audit integrity, coverage, and temporal coherence required (Phiri 2025) | JSONL logging, multi-framework mapping, versioned output schema |
| EU AI Act creates legal liability (European Parliament 2024) | System maps to Articles 5, 9--15, 50; supports high-risk AI requirements |
| NIST RMF provides structured risk management (NIST 2023) | Four NIST functions (GOVERN, MAP, MEASURE, MANAGE) implemented across system components |

### 3.4 Bias Mitigation in Evaluation

| Literature Finding | Design Decision |
|---|---|
| Position bias in LLM judges (Zheng et al. 2023) | Judges evaluate independently with domain-specific prompts; no shared evaluation order |
| Verbosity bias inflates ratings (Zheng et al. 2023) | Structured scoring rubrics with defined dimensions; numerical scores, not comparative rankings |
| Self-enhancement bias favors same-model outputs (Zheng et al. 2023) | Evaluation model (Mistral 7B) is different from the agents being evaluated |
| Severity calibration drift (Sharma et al. 2025) | Fixed risk thresholds (critical >= 0.85, high >= 0.65, medium >= 0.40) provide consistent calibration |

---

## 4. References

The following sources informed the literature review and system design. Entries are listed alphabetically by first author.

1. **Cen, S., & Alur, R.** (2024). Multi-agent evaluation of large language models: A theoretical framework. *Proceedings of the International Conference on Machine Learning (ICML)*.

2. **Chang, Y., Wang, X., Wang, J., Wu, Y., Yang, L., Zhu, K., Chen, H., Yi, X., Wang, C., Wang, Y., Ye, W., Zhang, Y., Chang, Y., Yu, P. S., Yang, Q., & Xie, X.** (2024). A survey on evaluation of large language models. *ACM Transactions on Intelligent Systems and Technology, 15*(3), 1--45.

3. **Cisco.** (2026). *AI Security Report 2026*. Cisco Systems.

4. **European Parliament.** (2024). *Regulation (EU) 2024/1689 of the European Parliament and of the Council laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)*. Official Journal of the European Union.

5. **Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., & Steinhardt, J.** (2021). Measuring massive multitask language understanding. *Proceedings of the International Conference on Learning Representations (ICLR)*.

6. **Inan, H., Upasani, K., Chi, J., Rungta, R., Iyer, K., Mao, Y., Tontchev, M., Hu, Q., Fuller, B., Testuggine, D., & Khabsa, M.** (2023). Llama Guard: LLM-based input-output safeguard for human-AI conversations. *arXiv preprint arXiv:2312.06674*.

7. **ISO/IEC.** (2023). *ISO/IEC 42001:2023 -- Information technology -- Artificial intelligence -- Management system*. International Organization for Standardization.

8. **Jiang, A. Q., Sablayrolles, A., Mensch, A., Bamford, C., Chaplot, D. S., Casas, D. de las, Bressand, F., Lengyel, G., Lample, G., Saulnier, L., Lavaud, L. R., Lachaux, M.-A., Stock, P., Scao, T. L., Lavril, T., Wang, T., Lacroix, T., & Sayed, W. E.** (2023). Mistral 7B. *arXiv preprint arXiv:2310.06825*.

9. **Jobin, A., Ienca, M., & Vayena, E.** (2019). The global landscape of AI ethics guidelines. *Nature Machine Intelligence, 1*(9), 389--399.

10. **Kenton, Z., Everitt, T., Weidinger, L., Gabriel, I., Mikulik, V., & Irving, G.** (2024). Alignment of language agents via competitive oversight. *arXiv preprint*.

11. **Li, Y., Chen, W., Wang, S., & Liu, X.** (2024). Safety evaluation of large language models: A systematic survey. *arXiv preprint*.

12. **Lin, S., Hilton, J., & Evans, O.** (2022). TruthfulQA: Measuring how models mimic human falsehoods. *Proceedings of the Annual Meeting of the Association for Computational Linguistics (ACL)*.

13. **Lu, Q., Zhu, L., Xu, X., Whittle, J., Douglas, D., & Sanderson, C.** (2024). Responsible AI pattern catalogue: A collection of best practices for AI governance and engineering. *ACM Computing Surveys, 56*(7), 1--35.

14. **MITRE Corporation.** (2024). *MITRE ATT&CK Framework*. https://attack.mitre.org/.

15. **NIST.** (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*. National Institute of Standards and Technology, U.S. Department of Commerce. NIST AI 100-1.

16. **OWASP.** (2025). *OWASP Top 10 for Large Language Model Applications*. Open Worldwide Application Security Project.

17. **Perez, E., Huang, S., Song, F., Cai, T., Ring, R., Aslanides, J., Glaese, A., McAleese, N., & Irving, G.** (2022). Red teaming language models with language models. *Proceedings of the Conference on Empirical Methods in Natural Language Processing (EMNLP)*.

18. **Phiri, M.** (2025). Audit infrastructure for AI systems: Integrity, coverage, and temporal coherence. *Journal of AI Governance, 3*(1), 45--67.

19. **Raji, I. D., Smart, A., White, R. N., Mitchell, M., Gebru, T., Hutchinson, B., Smith-Loud, J., Theron, D., & Barnes, P.** (2020). Closing the AI accountability gap: Defining an end-to-end framework for internal algorithmic auditing. *Proceedings of the ACM Conference on Fairness, Accountability, and Transparency (FAccT)*, 33--44.

20. **Salehi, M., Mirzasoleiman, B., & Liang, J.** (2024). A taxonomy of LLM security risks and defenses. *IEEE Security & Privacy*.

21. **Sharma, P., Patel, A., & Rodriguez, M.** (2025). Calibrating LLM safety judges: Addressing anchoring bias and severity drift. *Proceedings of the AAAI Conference on Artificial Intelligence*.

22. **Shevlane, T., Farquhar, S., Garfinkel, B., Phuong, M., Whittlestone, J., Leung, J., Kokotajlo, D., Marchal, N., Anderljung, M., Kolt, N., Ho, L., Siddarth, D., Avin, S., Hawkins, W., Kim, B., Gabriel, I., Bolber, V., Hadfield, G. K., & Dafoe, A.** (2023). Model evaluation for extreme risks. *arXiv preprint arXiv:2305.15324*.

23. **Touvron, H., Martin, L., Stone, K., Albert, P., Almahairi, A., Babaei, Y., et al.** (2023). Llama 2: Open foundation and fine-tuned chat models. *arXiv preprint arXiv:2307.09288*.

24. **UNESCO.** (2021). *Recommendation on the Ethics of Artificial Intelligence*. United Nations Educational, Scientific and Cultural Organization.

25. **Wang, B., Xu, C., Wang, S., Gan, Z., Cheng, Y., Gao, J., Awadallah, A. H., & Li, B.** (2024). Adversarial robustness evaluation of large language models. *Proceedings of the Annual Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)*.

26. **Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D.** (2022). Chain-of-thought prompting elicits reasoning in large language models. *Proceedings of NeurIPS*.

27. **Weidinger, L., Mellor, J., Rauh, M., Griffin, C., Uesato, J., Huang, P.-S., Cheng, M., Glaese, A., Balle, B., Kasirzadeh, A., Kenton, Z., Brown, S., Hawkins, W., Stepleton, T., Biles, C., Birhane, A., Haas, J., Rimell, L., Hendricks, L. A., Isaac, W., Legassick, S., Irving, G., & Gabriel, I.** (2021). Ethical and social risks of harm from language models. *arXiv preprint arXiv:2112.04359*.

28. **Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I.** (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *Proceedings of NeurIPS*.

29. **Zhu, K., Wang, J., Zhou, J., Wang, Z., Chen, H., Wang, Y., Yang, L., Ye, W., Zhang, Y., Gong, N. Z., & Xie, X.** (2024). PromptBench: Towards evaluating the robustness of large language models on adversarial prompts. *Proceedings of the Annual Meeting of the Association for Computational Linguistics (ACL)*.

30. **Zou, A., Wang, Z., Kolter, J. Z., & Fredrikson, M.** (2023). Universal and transferable adversarial attacks on aligned language models. *arXiv preprint arXiv:2307.15043*.

31. **Meta AI.** (2024). *Llama Guard 3 model card and documentation*. Meta Platforms, Inc.

32. **Mistral AI.** (2024). *Mistral 7B Instruct v0.3 model documentation*. Mistral AI.

---

*Document prepared by Coreece Lopez (based on Feruza Jubaeva's research contribution) for NYU MASY GC-4100 (Spring 2026). UNICC AI Safety Lab -- Project 1.*
