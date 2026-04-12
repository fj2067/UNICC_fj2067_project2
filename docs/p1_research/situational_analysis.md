# Situational Analysis -- UNICC AI Safety Lab

**Project 1**

| Field | Detail |
|---|---|
| **Author** | Coreece Lopez (based on Feruza Jubaeva's research contribution) |
| **Course** | NYU MASY GC-4100 -- Spring 2026 |
| **Date** | March 16, 2026 |
| **Last Updated** | April 7, 2026 |
| **Version** | 2.0 |

---

## 1. Industry Definition

The UNICC AI Safety Lab operates at the intersection of two domains:

1. **Intergovernmental Digital Infrastructure.** UNICC is the shared-services ICT provider for the United Nations system, serving 50+ organizations including UNHCR, WHO, UNICEF, WFP, and ITU. Its mandate is to deliver secure, reliable, and cost-effective digital infrastructure that enables UN agencies to focus on their humanitarian and development missions.

2. **AI Governance and Safety.** The AI Safety Lab addresses the emerging need for pre-deployment evaluation of AI agents within this intergovernmental context. As UN agencies accelerate AI adoption, UNICC's role expands from traditional IT services (hosting, networking, cybersecurity) to AI governance services (safety evaluation, compliance verification, risk assessment).

This positions the AI Safety Lab within the nascent **AI assurance** industry -- a market segment focused on verifying that AI systems meet safety, security, ethical, and regulatory requirements before deployment.

---

## 2. External Forces Analysis

### 2.1 AI Adoption Pressure

The speed and breadth of AI adoption creates urgency for safety evaluation capabilities.

| Statistic | Source | Implication |
|---|---|---|
| **78% of organizations** are now using AI in some operational capacity | Cisco AI Security Report 2026 | The UN system is not exempt. AI is being deployed across humanitarian logistics, document processing, translation, and data analysis. |
| **67% of organizations** plan to deploy AI agents (autonomous systems) within 24 months | Industry surveys, 2025--2026 | Agentic AI introduces higher-risk capabilities: tool use, code execution, and autonomous decision-making. |
| **42% increase** in AI-related incidents year-over-year | Multiple cybersecurity reports | More deployments mean more failures. Pre-deployment evaluation becomes essential. |

### 2.2 Readiness Gap

Organizations are adopting AI faster than they can secure it.

| Statistic | Source | Implication |
|---|---|---|
| **83% of organizations** plan to deploy AI agents | Industry surveys | Demand for agentic AI is overwhelming. |
| **Only 31%** can adequately secure their AI deployments | Cisco AI Security Report 2026 | A 52-percentage-point gap between ambition and capability. |
| **Less than 20%** have dedicated AI safety evaluation processes | Enterprise AI governance surveys | Most organizations rely on ad hoc review or vendor self-certification. |

This readiness gap is particularly acute in the UN system, where:
- AI adoption decisions are often made at the agency level without centralized safety review.
- Agency IT teams have cybersecurity expertise but may lack AI-specific safety knowledge.
- Vendor AI products are deployed with varying levels of safety documentation.
- The consequences of AI failures (in humanitarian, health, or peacekeeping contexts) are severe.

### 2.3 Security Threats

The threat landscape for LLM-based systems is evolving rapidly.

| Threat Category | Examples | Relevance to UNICC |
|---|---|---|
| **Prompt Injection** | Direct override, indirect injection via document content, multi-turn manipulation | AI agents processing UN documents could be manipulated through injected instructions in source materials. |
| **Jailbreak Attacks** | Persona adoption (DAN, AIM), encoding bypass (base64), roleplay exploitation | Agents deployed in sensitive UN contexts must resist attempts to bypass safety controls. |
| **Data Exfiltration** | PII leakage, system prompt extraction, training data extraction | UN agencies handle sensitive beneficiary data (refugees, patients, children) that must not be exposed. |
| **Supply Chain** | Compromised model weights, malicious fine-tuning, backdoored training data | Open-weight models used in UN systems must have verifiable provenance. |
| **Agentic Risks** | Unauthorized tool use, autonomous decision-making, external API calls | AI agents with execution capabilities can cause harm beyond information disclosure. |

### 2.4 Regulatory Hardening

Regulatory requirements for AI safety are intensifying globally.

| Regulation/Framework | Status | Key Requirement |
|---|---|---|
| **EU AI Act** | Effective 2024, phased enforcement through 2027 | High-risk AI systems must undergo conformity assessment including risk management, transparency, and human oversight. Penalties up to 35M EUR or 7% global revenue. |
| **NIST AI RMF** | Published 2023, voluntary adoption | Four-function framework (GOVERN, MAP, MEASURE, MANAGE) becoming a de facto standard for AI risk management. |
| **ISO/IEC 42001** | Published 2023, certification available | First international standard for AI management systems. Organizations seeking certification must demonstrate systematic AI risk management. |
| **UNESCO AI Ethics** | Adopted 2021, 193 member states | Binding on UN system organizations. Five principles: proportionality, fairness, privacy, transparency, human oversight. |
| **Executive Orders** | Various national approaches (US, UK, China, etc.) | Fragmented regulatory landscape increases compliance burden for international organizations. |

For UNICC, regulatory compliance is not optional. As a UN system organization, it is subject to UNESCO recommendations. As an organization serving EU-based agencies, it must consider EU AI Act requirements. As a technology provider, it must meet the expectations of agencies operating under diverse national regulations.

### 2.5 Trust and Accountability

Trust deficits threaten AI adoption in institutional contexts.

| Factor | Impact |
|---|---|
| **Public trust in AI is declining** | Surveys show growing public concern about AI safety, particularly in high-stakes domains (healthcare, criminal justice, social services). |
| **Institutional legitimacy is at stake** | UN agencies deploying unsafe AI risk reputational damage that undermines their mandates. |
| **Accountability mechanisms are underdeveloped** | Most AI systems lack audit trails, explainable verdicts, and clear chains of responsibility. |
| **Stakeholder expectations are rising** | Member states, donors, and beneficiaries increasingly expect responsible AI governance. |

---

## 3. Competitor and Substitute Analysis

The AI Safety Lab does not operate in a commercial market, but UNICC faces alternatives (build, buy, or abstain) for AI safety evaluation. Understanding these alternatives informs the value proposition.

### Competitive Landscape

| Category | Solution | Strengths | Weaknesses | Fit for UNICC |
|---|---|---|---|---|
| **Unified AI Governance Platforms** | IBM Watsonx.governance | Enterprise-grade; integrated with IBM AI stack; comprehensive monitoring | Vendor lock-in; expensive licensing; requires IBM ecosystem; limited customization for UN context | **Low.** Licensing costs, vendor dependency, and lack of UN-specific governance alignment make this impractical for UNICC's shared-services model. |
| **Unified AI Governance Platforms** | Microsoft Responsible AI Toolkit | Integrated with Azure; strong documentation; fairness/transparency tools | Tied to Microsoft ecosystem; limited adversarial testing; compliance focus on US/EU only | **Medium.** UNICC uses Microsoft services, but the toolkit lacks the multi-framework governance alignment and adversarial security testing required. |
| **AI-Native Security** | Lakera Guard | Purpose-built for LLM security; fast prompt injection detection; API-based | Narrow focus (security only, not ethics/governance); SaaS dependency; data leaves organization | **Low.** Security-only scope misses ethics and governance requirements. SaaS model raises data sovereignty concerns for UN operations. |
| **AI-Native Security** | Protect AI | ML supply chain security; model scanning; vulnerability detection | Early-stage product; limited LLM-specific capabilities; primarily supply chain focused | **Low.** Supply chain focus is valuable but insufficient as a complete evaluation solution. |
| **AI Evaluation** | Patronus AI | LLM evaluation platform; hallucination detection; safety benchmarks | Commercial SaaS; US-focused regulatory alignment; limited customization | **Medium.** Strong evaluation capabilities but lacks UN-specific governance and multi-framework alignment. |
| **Cloud Guardrails** | AWS Bedrock Guardrails | Native AWS integration; content filtering; PII detection | Tied to AWS ecosystem; limited adversarial testing; basic rule-based filtering | **Low.** AWS dependency conflicts with UNICC's multi-cloud and vendor-neutral posture. |
| **Cloud Guardrails** | Azure AI Content Safety | Content classification; severity scoring; customizable categories | Microsoft ecosystem dependency; limited to content safety (not governance or security) | **Low.** Content safety only; no adversarial testing, governance alignment, or multi-framework compliance. |
| **Manual Review** | Human expert review | High accuracy for nuanced judgments; contextual understanding; stakeholder trust | Extremely slow (hours per evaluation); expensive; does not scale; reviewer fatigue; inconsistent | **Partial.** Necessary for high-risk determinations but unsustainable as the sole evaluation method for growing AI deployments. |

### Key Differentiators of the AI Safety Lab

| Differentiator | AI Safety Lab | Commercial Alternatives |
|---|---|---|
| **Multi-framework governance** | Maps to 6 frameworks simultaneously (OWASP, MITRE, EU AI Act, NIST RMF, ISO 42001, UNESCO) | Typically 1--2 frameworks, often US/EU-centric |
| **Three-judge council** | Independent security, ethics, and governance evaluation with structured arbitration | Single-model evaluation or rule-based filtering |
| **UN context alignment** | Designed for UNICC's shared-services model, multilateral stakeholder environment, and humanitarian mission | Designed for commercial enterprises |
| **Open-weight models** | Llama Guard 3, Mistral 7B -- auditable, no vendor lock-in, no data exfiltration | Often proprietary models or SaaS dependencies |
| **Data sovereignty** | All evaluation runs on-premises (DGX Spark); no data leaves the cluster | SaaS solutions require data transmission to third-party servers |
| **Cost** | Open-weight models + existing GPU infrastructure = marginal operational cost | Licensing fees of $50K--$500K+ annually |

---

## 4. Internal Environment

### 4.1 UNICC Stakeholder Analysis

| Stakeholder Group | Role | Needs | Influence |
|---|---|---|---|
| **IT Developers** | Build and deploy AI agents for UN agencies | Fast, actionable feedback on agent safety before deployment; clear remediation guidance | **High.** Primary users of the evaluation system. Their adoption determines system success. |
| **UNICC AI Hub** | Centralized AI governance and innovation within UNICC | Standardized evaluation process; governance compliance evidence; scalable solution | **High.** Institutional sponsor. AI Hub mandate aligns directly with the Safety Lab's purpose. |
| **UN Partner Agencies** | Consume AI-powered services from UNICC | Assurance that AI agents meet safety, ethical, and regulatory standards; transparency about evaluation process | **High.** Ultimate beneficiaries. Their trust in UNICC's AI services depends on demonstrable safety governance. |
| **UNICC Management** | Oversee UNICC operations and strategic direction | Cost-effective solution; reputational risk mitigation; alignment with UNICC's shared-services mandate | **Medium.** Strategic decision-makers who allocate resources and set organizational priorities. |
| **Member State Representatives** | Govern UN system organizations | Accountability for AI use in their organizations; compliance with national and international regulations | **Medium.** Indirect but powerful influence through governance bodies and budget decisions. |
| **Beneficiary Populations** | End users of UN services powered by AI | Safety and fairness; no discrimination; privacy protection; accurate and helpful AI interactions | **Low** (direct influence) but **High** (moral imperative). The AI Safety Lab exists to protect vulnerable populations served by the UN. |

### 4.2 Shared-Services Model Fit

UNICC's shared-services model is a natural fit for centralized AI safety evaluation:

1. **Economies of scale.** A single evaluation system serves 50+ organizations, avoiding duplicative investment in safety infrastructure.
2. **Consistency.** Centralized evaluation ensures uniform safety standards across the UN system, preventing a "race to the bottom" where agencies with fewer resources deploy less-evaluated AI.
3. **Expertise concentration.** AI safety is a specialized domain. Centralizing expertise at UNICC is more efficient than distributing it across dozens of agencies.
4. **Governance simplification.** A single point of evaluation simplifies compliance reporting for multiple frameworks and jurisdictions.
5. **Precedent.** UNICC already provides centralized cybersecurity, hosting, and network services. AI safety evaluation is a natural extension of this portfolio.

---

## 5. Strategic Analysis Tools

### 5.1 SWOT Analysis

#### Strengths

| Strength | Description |
|---|---|
| **Institutional mandate** | UNICC's role as the UN system's shared ICT provider gives it legitimate authority to establish AI safety standards. |
| **Existing infrastructure** | DGX Spark cluster provides substantial GPU resources (128 GB) without additional capital investment. |
| **Open-weight models** | Llama Guard 3 and Mistral 7B eliminate vendor lock-in and licensing costs. Models are auditable and modifiable. |
| **Multi-framework alignment** | System maps to 6 governance frameworks, satisfying diverse regulatory and ethical requirements. |
| **Three-judge architecture** | Council-of-experts design is backed by research (Kenton et al. 2024, Cen & Alur 2024) and addresses known LLM-as-judge biases. |
| **Data sovereignty** | On-premises evaluation ensures sensitive UN data never leaves the cluster. |

#### Weaknesses

| Weakness | Description |
|---|---|
| **Resource constraints** | Three-student project team with limited development time (one semester). |
| **Model limitations** | Mistral 7B is a 7-billion-parameter model; larger models could provide more nuanced reasoning for complex safety judgments. |
| **Single-cluster dependency** | System depends on NYU DGX Spark availability. No failover cluster is configured. |
| **Limited multilingual capability** | Current detection patterns and judge prompts are English-centric. UN operates in six official languages. |
| **No production hardening** | System is a capstone project, not a production-hardened service. Additional engineering would be needed for 24/7 operation. |

#### Opportunities

| Opportunity | Description |
|---|---|
| **Regulatory demand** | EU AI Act enforcement (2025--2027) creates urgent demand for AI evaluation capabilities across the UN system. |
| **UNICC AI Hub expansion** | The AI Hub's growing mandate could provide institutional backing for productionizing the Safety Lab. |
| **Open-source contribution** | The evaluation architecture and governance mappings could be open-sourced, establishing UNICC as a thought leader in AI governance. |
| **Multi-agency adoption** | Success at UNICC could lead to adoption across 50+ UN agencies, creating a de facto standard for intergovernmental AI safety. |
| **Model upgrades** | As open-weight models improve (Llama 4, Mistral Large), the system can upgrade its reasoning capabilities without architectural changes. |

#### Threats

| Threat | Description |
|---|---|
| **Evolving attack landscape** | New prompt injection and jailbreak techniques may outpace the Security Judge's detection patterns. |
| **Commercial competition** | Enterprise AI governance platforms (IBM, Microsoft) may offer integrated solutions that appeal to UN procurement. |
| **Regulatory fragmentation** | Divergent national AI regulations could complicate multi-framework compliance for an international organization. |
| **Stakeholder resistance** | IT developers may view safety evaluation as a bottleneck rather than a value-add. Adoption requires careful change management. |
| **Resource allocation** | Competing priorities within UNICC may limit investment in AI safety infrastructure. |

### 5.2 Porter's Five Forces -- Adapted for UNICC Context

Porter's Five Forces framework is adapted here for UNICC's non-commercial, intergovernmental context.

#### Force 1: Threat of New Entrants (Medium)

| Factor | Assessment |
|---|---|
| Barriers to entry | **Medium.** Building an AI evaluation system requires specialized expertise, but open-weight models and cloud GPUs lower the technical barrier. |
| Capital requirements | **Low.** Open-weight models and existing GPU infrastructure minimize upfront investment. |
| Regulatory barriers | **High.** Multi-framework compliance (6 frameworks) creates a significant knowledge barrier. |
| Assessment | Individual UN agencies could build their own evaluation systems, but the complexity of multi-framework compliance and the cost of duplicative infrastructure make centralized provision more efficient. |

#### Force 2: Bargaining Power of Suppliers (Low)

| Factor | Assessment |
|---|---|
| Model suppliers | **Low.** Open-weight models (Meta Llama Guard, Mistral) have no licensing leverage. Alternative models are readily available. |
| Infrastructure suppliers | **Medium.** DGX Spark is provided by NYU. Long-term, UNICC would need its own GPU infrastructure or cloud GPU access. |
| Assessment | Open-weight model strategy deliberately minimizes supplier power. No single supplier can hold the system hostage. |

#### Force 3: Bargaining Power of Buyers (High)

| Factor | Assessment |
|---|---|
| UN agency autonomy | **High.** Agencies can choose whether to use UNICC's evaluation service or build/buy their own. |
| Switching costs | **Low.** Evaluation is a service, not a deeply embedded platform. Agencies can switch to alternatives relatively easily. |
| Assessment | High buyer power means the system must deliver clear value (speed, comprehensiveness, compliance evidence) to drive voluntary adoption. |

#### Force 4: Threat of Substitutes (High)

| Factor | Assessment |
|---|---|
| Manual review | Existing substitute. Slow and expensive but trusted by stakeholders accustomed to human judgment. |
| Commercial platforms | Growing substitute. IBM, Microsoft, and AI-native security vendors offer alternatives with enterprise support. |
| No evaluation | The most dangerous substitute. Agencies may skip evaluation entirely under time pressure. |
| Assessment | The system must be faster than manual review, more customizable than commercial platforms, and more trustworthy than no evaluation. |

#### Force 5: Competitive Rivalry (Low-Medium)

| Factor | Assessment |
|---|---|
| Internal competition | **Low.** No other UNICC team is building an AI safety evaluation system. |
| External competition | **Medium.** Commercial vendors are entering the AI governance space, but none offer UN-specific alignment. |
| Assessment | Current rivalry is low, but the window of opportunity is time-limited. Early establishment of the Safety Lab creates institutional precedent. |

---

## 6. Conclusion

The situational analysis supports the following conclusions:

1. **Pre-deployment AI safety evaluation is strategically sound.** The convergence of adoption pressure (78% of organizations using AI), the readiness gap (83% plan agents, only 31% can secure them), regulatory hardening (EU AI Act, UNESCO, NIST), and the evolving threat landscape creates an urgent need for systematic evaluation.

2. **UNICC is the right organization to provide this service.** Its shared-services mandate, existing infrastructure, institutional legitimacy, and stakeholder relationships position it uniquely within the UN system.

3. **The AI Safety Lab's architecture is competitively differentiated.** Multi-framework governance alignment (6 frameworks), three-judge council design (research-backed), open-weight models (no vendor lock-in), and on-premises data sovereignty (UN-appropriate) distinguish it from commercial alternatives.

4. **Key risks are manageable.** Resource constraints are addressed through the modular project sequence (P1 -> P2 -> P3). Model limitations can be addressed through future upgrades. The evolving threat landscape requires ongoing detection pattern updates, which the modular judge architecture supports.

5. **Adoption will require active stakeholder engagement.** High buyer power and the availability of substitutes (including doing nothing) mean that the system must demonstrate clear, immediate value to IT developers and agency decision-makers.

The AI Safety Lab is not just a technical system; it is a governance capability. Its value lies not only in detecting unsafe AI agents but in providing the institutional framework -- the audit trails, the compliance evidence, the multi-framework alignment, and the human oversight triggers -- that enables UNICC and the broader UN system to adopt AI responsibly.

---

*Document prepared by Coreece Lopez (based on Feruza Jubaeva's research contribution) for NYU MASY GC-4100 (Spring 2026). UNICC AI Safety Lab -- Project 1.*
