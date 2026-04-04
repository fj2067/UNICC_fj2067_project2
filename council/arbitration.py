def council_decision(results):

    unsafe_votes = sum(r["verdict"] == "unsafe" for r in results)

    avg_score = sum(r["score"] for r in results) / len(results)

    if unsafe_votes >= 2:
        verdict = "UNSAFE"
    else:
        verdict = "SAFE"

    return {
        "final_verdict": verdict,
        "average_score": avg_score
    }
