from input_layer.loader import load_input
from judges.technical_judge import SecurityJudge
from judges.governance_judge import GovernanceJudge
from judges.ethics_judge import EthicsJudge
from council.moe_council import SafetyCouncil
from council.arbitration import council_decision
from output.report import generate_report

def main():

    text = load_input()

    judges = [
        SecurityJudge(),
        GovernanceJudge(),
        EthicsJudge()
    ]

    council = SafetyCouncil(judges)

    results = council.evaluate(text)

    decision = council_decision(results)

    report = generate_report(text, results, decision)

    print("\nSAFETY REPORT")
    print(report)

if __name__ == "__main__":
    main()
