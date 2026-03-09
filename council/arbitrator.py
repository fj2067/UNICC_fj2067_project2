from judges import judge_technical, judge_policy, judge_ethics

def council_evaluate(prompt):

    results = [
        technical_judge.evaluate(prompt),
        legal_judge.evaluate(prompt),
        ethics_judge.evaluate(prompt)
    ]

    avg_score = sum(r["risk_score"] for r in results) / len(results)

    return {
        "council_score": avg_score,
        "judge_outputs": results
    }
