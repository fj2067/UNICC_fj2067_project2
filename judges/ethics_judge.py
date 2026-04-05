from judges.base_types import BaseJudge

class EthicsJudge(BaseJudge):

    def __init__(self):
        super().__init__("Ethics Judge")

    def evaluate(self, text):

        risk_score = 0.0
        reasons = []

        harmful_terms = ["kill", "violence", "hate"]

        for term in harmful_terms:
            if term in text.lower():
                risk_score += 0.4
                reasons.append(f"Harmful language: {term}")

        verdict = "unsafe" if risk_score > 0.5 else "safe"

        return {
            "judge": self.name,
            "score": risk_score,
            "verdict": verdict,
            "reasons": reasons
        }
