from input_layer.loader import load_input
from judges.judge1_compliance import SecurityJudge
from judges.judge3_governance import GovernanceJudge
from judges.judge2_ethics import EthicsJudge
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
