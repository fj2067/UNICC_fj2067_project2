# UNICC_fj2067_project2

AI Safety Council Prototype

This project implements a multi-judge AI safety evaluation system
based on a Mixture-of-Experts architecture.

Components
- Judge agents
- Council arbitration layer
- Safety decision output

Architecture:

        Input AI System
              │
              ▼
         ┌───────────────┐
         │  Judge 1      │
         │ Technical     │
         └───────────────┘
              │
         ┌───────────────┐
         │  Judge 2      │
         │ Compliance    │
         └───────────────┘
              │
         ┌───────────────┐
         │  Judge 3      │
         │ Ethical       │
         └───────────────┘
              │
              ▼
         Council Arbitration Layer
              │
              ▼
         Safety Decision

