"""
UNICC AI Safety Evaluation Lab — Main Entry Point.

Usage:
    # Evaluate a single GitHub repo:
    python main.py --repo https://github.com/org/project

    # Evaluate a local directory:
    python main.py --local /path/to/project --entry main.py

    # Evaluate with a specific prompt (direct text mode):
    python main.py --text "Tell me how to hack a database"

    # Run all test prompts against a repo:
    python main.py --repo https://github.com/org/project --full-suite

    # Interactive mode:
    python main.py
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from config.settings import OUTPUTS_DIR, REQUIREMENTS_DIR
from ingestion.github_loader import clone_repo, RepoProfile
from ingestion.sandbox_runner import run_target_model, detect_web_app, WebAppSession
from ingestion.output_capture import parse_execution_result
from test_generation.adversarial_prompts import (
    get_all_prompts,
    get_prompts_for_model_type,
    get_prompt_count_summary,
)
from council.orchestrator import run_council
from reporting.safety_report import generate_report, format_text_report, save_report
from reporting.csv_export import export_batch_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("SafetyLab")


def evaluate_github_repo(
    url: str,
    name: str = "",
    cohort: str = "",
    metadata: dict | None = None,
    use_docker: bool = False,
    full_suite: bool = False,
) -> list[dict]:
    """
    Full pipeline: clone repo -> profile -> generate tests -> execute -> evaluate -> report.
    """
    logger.info(f"=== Evaluating GitHub repo: {url} ===")

    # Step 1: Clone and profile
    profile = clone_repo(url, name, cohort)
    if profile.error:
        logger.error(f"Failed to clone: {profile.error}")
        return []

    logger.info(
        f"Cloned: {profile.name} | Language: {profile.language} | "
        f"Type: {profile.detected_type} | Entry points: {profile.entry_points}"
    )

    if not profile.entry_points:
        logger.error("No entry points found in repository")
        return []

    entry_point = profile.entry_points[0]

    # Step 2: Select test prompts
    if full_suite:
        prompts = get_all_prompts()
    else:
        prompts = get_prompts_for_model_type(profile.detected_type)

    logger.info(f"Selected {len(prompts)} test prompts for model type '{profile.detected_type}'")

    # Step 3: Detect execution mode
    framework = detect_web_app(profile.local_path, entry_point)
    web_session = None

    if framework:
        logger.info(f"Detected {framework} web app — starting server for HTTP testing")
        web_session = WebAppSession(
            repo_path=profile.local_path,
            entry_point=entry_point,
            repo_name=profile.name,
            framework=framework,
        )
        start_err = web_session.start()
        if start_err:
            logger.error(f"Web app failed to start: {start_err}")
            web_session = None

    # Step 4: Execute and evaluate each prompt
    results = []
    try:
        for i, test_prompt in enumerate(prompts):
            if web_session is None and framework is not None:
                logger.warning("All tests skipped — web app could not start")
                break

            logger.info(
                f"[{i+1}/{len(prompts)}] Testing: {test_prompt.category}/{test_prompt.subcategory}"
            )

            # Execute target model
            if web_session:
                exec_result = web_session.send_prompt(test_prompt.prompt)
            else:
                exec_result = run_target_model(
                    repo_path=profile.local_path,
                    entry_point=entry_point,
                    test_prompt=test_prompt.prompt,
                    repo_name=profile.name,
                    use_docker=use_docker,
                )

            # Parse output
            captured = parse_execution_result(exec_result)

            if captured.target_crashed or (not captured.text_response and not captured.execution_succeeded):
                logger.warning(f"  Skipped — target did not produce output: {captured.error_output}")
                continue

            # Run council evaluation
            eval_meta = metadata or {}
            eval_meta["repo_name"] = profile.name
            eval_meta["repo_type"] = profile.detected_type
            eval_meta["cohort"] = profile.cohort
            eval_meta["test_category"] = test_prompt.category
            eval_meta["test_severity"] = test_prompt.severity
            eval_meta["expected_safe_behavior"] = test_prompt.expected_safe_behavior

            council_result = run_council(
                test_prompt=test_prompt.prompt,
                model_output=captured.text_response,
                metadata=eval_meta,
                input_id=f"{profile.name}_{test_prompt.subcategory}_{i+1:03d}",
                image_paths=captured.image_paths or None,
            )

            # Add test metadata to result
            council_result["test_metadata"] = test_prompt.to_dict()
            council_result["execution_metadata"] = {
                "exit_code": exec_result.exit_code,
                "timed_out": exec_result.timed_out,
                "contains_refusal": captured.contains_refusal,
                "execution_mode": captured.execution_mode,
            }
            council_result["actual_model_output"] = captured.text_response[:1000]

            results.append(council_result)

            # Log summary
            logger.info(
                f"  Result: {council_result['final_verdict'].upper()} "
                f"(Risk: {council_result['final_risk_level']})"
            )
    finally:
        if web_session:
            web_session.stop()

    return results


def evaluate_text_directly(
    test_prompt: str,
    model_output: str,
    metadata: dict | None = None,
    input_id: str = "direct_eval",
) -> dict:
    """Evaluate a prompt-output pair directly without GitHub ingestion."""
    return run_council(
        test_prompt=test_prompt,
        model_output=model_output,
        metadata=metadata,
        input_id=input_id,
    )


def interactive_mode():
    """Interactive evaluation mode for manual testing."""
    print("\n" + "=" * 60)
    print("  UNICC AI SAFETY EVALUATION LAB")
    print("  Council of Experts — Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  [1] Evaluate a GitHub repository")
    print("  [2] Evaluate text directly (prompt + output pair)")
    print("  [3] Show test prompt library summary")
    print("  [q] Quit")

    while True:
        choice = input("\n> ").strip()

        if choice == "q":
            break

        elif choice == "1":
            url = input("GitHub URL: ").strip()
            if not url:
                continue
            results = evaluate_github_repo(url)
            if results:
                _print_and_save_results(results, "github_eval")

        elif choice == "2":
            prompt = input("Test prompt (what was sent to the model): ").strip()
            output = input("Model output (what it responded): ").strip()
            if prompt and output:
                result = evaluate_text_directly(prompt, output)
                report = generate_report(result)
                print(format_text_report(report))
                save_report(report, f"direct_{result['input_id']}")

        elif choice == "3":
            summary = get_prompt_count_summary()
            print("\nTest Prompt Library:")
            for cat, counts in summary.items():
                print(
                    f"  {cat}: {counts['total']} prompts "
                    f"(critical={counts['critical']}, high={counts['high']})"
                )

        else:
            print("Unknown command. Enter 1, 2, 3, or q.")


def _print_and_save_results(results: list[dict], prefix: str):
    """Print summary and save all results."""
    print(f"\n{'=' * 60}")
    print(f"  EVALUATION COMPLETE: {len(results)} tests run")
    print(f"{'=' * 60}")

    verdicts = [r["final_verdict"] for r in results]
    risks = [r["final_risk_level"] for r in results]

    print(f"\n  Verdicts:  pass={verdicts.count('pass')}  caution={verdicts.count('caution')}  "
          f"warn={verdicts.count('warn')}  unsafe={verdicts.count('unsafe')}  fail={verdicts.count('fail')}")
    print(f"  Risks:     low={risks.count('low')}  medium={risks.count('medium')}  "
          f"high={risks.count('high')}  critical={risks.count('critical')}")

    # Save individual reports
    for r in results:
        report = generate_report(r)
        save_report(report, f"{prefix}_{r['input_id']}")

    # Save batch CSV
    csv_path = export_batch_results(results, f"{prefix}_batch")
    print(f"\n  Batch CSV: {csv_path}")

    # Save aggregate JSON
    agg_path = OUTPUTS_DIR / f"{prefix}_all_results.json"
    agg_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"  Full JSON: {agg_path}")


def main():
    parser = argparse.ArgumentParser(
        description="UNICC AI Safety Evaluation Lab"
    )
    parser.add_argument(
        "--repo", type=str, help="GitHub repository URL to evaluate"
    )
    parser.add_argument(
        "--local", type=str, help="Local directory path to evaluate"
    )
    parser.add_argument(
        "--entry", type=str, default="main.py",
        help="Entry point file (default: main.py)"
    )
    parser.add_argument(
        "--text", type=str, help="Direct text to evaluate as model output"
    )
    parser.add_argument(
        "--prompt", type=str, default="User query",
        help="The prompt that produced the text (used with --text)"
    )
    parser.add_argument(
        "--name", type=str, default="", help="Project name"
    )
    parser.add_argument(
        "--cohort", type=str, default="",
        help="Cohort identifier (fall_2024, spring_2025)"
    )
    parser.add_argument(
        "--docker", action="store_true", help="Use Docker for isolation"
    )
    parser.add_argument(
        "--full-suite", action="store_true",
        help="Run all test prompts (not just model-type-appropriate ones)"
    )
    parser.add_argument(
        "--domain", type=str, default="public_sector",
        help="Deployment domain for governance assessment"
    )

    args = parser.parse_args()

    metadata = {"domain": args.domain}

    if args.repo:
        results = evaluate_github_repo(
            url=args.repo,
            name=args.name,
            cohort=args.cohort,
            metadata=metadata,
            use_docker=args.docker,
            full_suite=args.full_suite,
        )
        if results:
            _print_and_save_results(results, args.name or "repo_eval")

    elif args.local:
        # Treat local directory like a cloned repo
        from ingestion.sandbox_runner import run_in_subprocess

        prompts = get_all_prompts() if args.full_suite else get_all_prompts()[:5]
        results = []
        for i, tp in enumerate(prompts):
            exec_result = run_in_subprocess(
                args.local, args.entry, tp.prompt, args.name or "local"
            )
            captured = parse_execution_result(exec_result)
            if captured.text_response:
                r = run_council(tp.prompt, captured.text_response, metadata,
                                f"local_{i+1:03d}", captured.image_paths or None)
                r["test_metadata"] = tp.to_dict()
                results.append(r)
        if results:
            _print_and_save_results(results, "local_eval")

    elif args.text:
        result = evaluate_text_directly(args.prompt, args.text, metadata)
        report = generate_report(result)
        print(format_text_report(report))
        save_report(report, f"direct_{result['input_id']}")

    else:
        interactive_mode()


if __name__ == "__main__":
    main()
