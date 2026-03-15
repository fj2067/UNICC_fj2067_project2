def generate_report(input_text, judge_results, council_result):

    report = {
        "input": input_text,
        "judges": judge_results,
        "final_verdict": council_result["final_verdict"],
        "risk_score": council_result["average_score"]
    }

    return report
