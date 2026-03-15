from judges.base_judge import BaseJudge

class GovernanceJudge(BaseJudge):

    def __init__(self):
        super().__init__("Governance Judge")

    def evaluate(self, text):

        risk_score = 0.0
        reasons = []

        if "social security" in text.lower():
            risk_score += 0.6
            reasons.append("Sensitive personal data")

        if "confidential" in text.lower():
            risk_score += 0.4
            reasons.append("Confidential data exposure")

        verdict = "unsafe" if risk_score > 0.5 else "safe"

        return {
            "judge": self.name,
            "score": risk_score,
            "verdict": verdict,
            "reasons": reasons
        }
