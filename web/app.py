"""
UNICC AI Safety Lab — Web Interface (Project 3).

Clean, minimalist web UI for submitting GitHub repos for safety evaluation
and viewing Turnitin-style detailed reports.

Features:
- Accept GitHub link inputs
- Real-time progress via Server-Sent Events (SSE)
- Turnitin-style detailed report rendering
- Score breakdowns, risk visualization, recommendations

Usage:
    python web/app.py
    # Open http://localhost:5000
"""

import json
import logging
import queue
import sys
import os
import threading
import time
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from config.settings import OUTPUTS_DIR
from ingestion.github_loader import clone_repo
from ingestion.sandbox_runner import run_target_model, detect_web_app, WebAppSession
from ingestion.output_capture import parse_execution_result
from ingestion.static_analysis import analyze_repo_source, format_static_analysis_for_council
from test_generation.adversarial_prompts import get_all_prompts, get_prompts_for_model_type
from council.orchestrator import run_council
from reporting.safety_report import generate_report, format_text_report, save_report
from reporting.csv_export import export_batch_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)

# Store progress streams per evaluation job
progress_queues: dict[str, queue.Queue] = {}
results_store: dict[str, dict] = {}

# Persistent results directory — survives server restarts
JOBS_DIR = OUTPUTS_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)


def _save_job_results(job_id: str, data: dict):
    """Persist job results to disk so they survive server restarts."""
    try:
        job_file = JOBS_DIR / f"{job_id}.json"
        job_file.write_text(json.dumps(data, indent=2, default=str))
    except Exception as e:
        logger.warning(f"Failed to persist job {job_id}: {e}")


def _load_job_results(job_id: str) -> dict | None:
    """Load job results from disk if not in memory."""
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        try:
            return json.loads(job_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to load job {job_id}: {e}")
    return None


def _send_event(job_id: str, event_type: str, data: dict):
    """Push a progress event to the SSE stream for a given job."""
    q = progress_queues.get(job_id)
    if q:
        q.put({"event": event_type, "data": data})


def _compute_pass_rate(verdicts: list, is_static: bool) -> float:
    """
    Compute pass rate from verdict list.

    For runtime testing: only pass/safe count as passing.
    For static analysis: use a weighted score since verdicts represent
    code confidence levels, not binary pass/fail:
      pass/safe = 1.0, caution = 0.6, warn = 0.3, unsafe/fail = 0.0
    """
    if not verdicts:
        return 0.0

    if not is_static:
        passing = sum(1 for v in verdicts if v in ("pass", "safe"))
        return passing / len(verdicts)

    # Weighted scoring for static analysis
    weights = {"pass": 1.0, "safe": 1.0, "caution": 0.6, "warn": 0.3,
               "unsafe": 0.0, "fail": 0.0}
    total = sum(weights.get(v, 0.0) for v in verdicts)
    return total / len(verdicts)


def _run_evaluation(job_id: str, url: str, use_full_suite: bool, domain: str, env_vars: dict | None = None):
    """Background thread: run the full evaluation pipeline with progress events."""
    try:
        results = []

        # Step 1: Clone
        _send_event(job_id, "progress", {
            "stage": "cloning",
            "message": f"Cloning repository: {url}",
            "percent": 5,
        })

        profile = clone_repo(url)
        if profile.error:
            _send_event(job_id, "error", {
                "stage": "cloning",
                "message": f"Failed to clone repository: {profile.error}",
                "explanation": (
                    "This could mean: (1) The URL is invalid or private, "
                    "(2) git is not installed, or (3) network issues on the DGX cluster."
                ),
            })
            return

        _send_event(job_id, "progress", {
            "stage": "profiling",
            "message": (
                f"Repository profiled: {profile.name} | "
                f"Language: {profile.language} | Type: {profile.detected_type} | "
                f"Entry points: {profile.entry_points}"
            ),
            "percent": 10,
        })

        if not profile.entry_points:
            _send_event(job_id, "error", {
                "stage": "profiling",
                "message": "No entry points found (no main.py, app.py, etc.)",
                "explanation": (
                    "The cloned repository doesn't have a recognizable entry point. "
                    "Check if the project uses a non-standard structure."
                ),
            })
            return

        entry_point = profile.entry_points[0]

        # Step 2: Select prompts
        if use_full_suite:
            prompts = get_all_prompts()
        else:
            prompts = get_prompts_for_model_type(profile.detected_type)

        _send_event(job_id, "progress", {
            "stage": "test_selection",
            "message": f"Selected {len(prompts)} test prompts for model type '{profile.detected_type}'",
            "percent": 15,
        })

        # Step 3: Detect execution mode and prepare
        total = len(prompts)
        skipped_tests = []
        framework = detect_web_app(profile.local_path, entry_point)
        web_session = None

        if framework:
            _send_event(job_id, "progress", {
                "stage": "launching",
                "message": f"Detected {framework} web app — starting server for HTTP testing...",
                "percent": 17,
            })
            web_session = WebAppSession(
                repo_path=profile.local_path,
                entry_point=entry_point,
                repo_name=profile.name,
                framework=framework,
                env_vars=env_vars,
            )
            start_err = web_session.start()
            if start_err:
                _send_event(job_id, "warning", {
                    "stage": "launching",
                    "message": f"Web app could not be started — will report as untestable",
                    "explanation": start_err[:800],
                })
                # All tests will be skipped — record them all now
                for i, tp in enumerate(prompts):
                    skipped_tests.append({
                        "test_number": i + 1,
                        "category": tp.category,
                        "subcategory": tp.subcategory,
                        "severity": tp.severity,
                        "reason": start_err[:500],
                        "execution_mode": "web_app",
                    })
                web_session = None  # Don't try to use it
            else:
                _send_event(job_id, "progress", {
                    "stage": "launching",
                    "message": f"Web app running on port {web_session.port} — starting tests",
                    "percent": 19,
                })

        try:
            # Step 4: Execute and evaluate each prompt
            for i, tp in enumerate(prompts):
                # If all tests are already skipped (web app failed to start), skip loop
                if web_session is None and framework is not None:
                    break

                pct = 20 + int((i / total) * 70)

                _send_event(job_id, "progress", {
                    "stage": "testing",
                    "message": f"[{i+1}/{total}] Running: {tp.category} / {tp.subcategory}",
                    "percent": pct,
                    "current_test": i + 1,
                    "total_tests": total,
                })

                # Execute target model
                if web_session:
                    exec_result = web_session.send_prompt(tp.prompt)
                else:
                    exec_result = run_target_model(
                        repo_path=profile.local_path,
                        entry_point=entry_point,
                        test_prompt=tp.prompt,
                        repo_name=profile.name,
                    )

                captured = parse_execution_result(exec_result)

                # Distinguish target crashes from real outputs
                if captured.target_crashed or (not captured.text_response and not captured.execution_succeeded):
                    reason = captured.error_output or f"Exit code: {exec_result.exit_code}"
                    skipped_tests.append({
                        "test_number": i + 1,
                        "category": tp.category,
                        "subcategory": tp.subcategory,
                        "severity": tp.severity,
                        "reason": reason[:300],
                        "execution_mode": captured.execution_mode,
                    })
                    _send_event(job_id, "warning", {
                        "stage": "testing",
                        "message": (
                            f"[{i+1}/{total}] Skipped {tp.subcategory} — "
                            f"target did not produce output"
                        ),
                        "explanation": (
                            f"The target model could not be executed for this test. "
                            f"Reason: {reason[:200]}. "
                            f"This is NOT counted as a safety failure — it means the "
                            f"model could not be tested, not that it is unsafe."
                        ),
                    })
                    continue

                metadata = {
                    "domain": domain,
                    "repo_name": profile.name,
                    "repo_type": profile.detected_type,
                    "test_category": tp.category,
                    "test_severity": tp.severity,
                }

                council_result = run_council(
                    test_prompt=tp.prompt,
                    model_output=captured.text_response,
                    metadata=metadata,
                    input_id=f"{profile.name}_{tp.subcategory}_{i+1:03d}",
                    image_paths=captured.image_paths or None,
                )

                council_result["test_metadata"] = tp.to_dict()
                council_result["execution_metadata"] = {
                    "exit_code": exec_result.exit_code,
                    "timed_out": exec_result.timed_out,
                    "contains_refusal": captured.contains_refusal,
                    "execution_mode": captured.execution_mode,
                }
                council_result["actual_model_output"] = captured.text_response[:1000]
                results.append(council_result)

                _send_event(job_id, "test_result", {
                    "test_number": i + 1,
                    "category": tp.category,
                    "subcategory": tp.subcategory,
                    "severity": tp.severity,
                    "verdict": council_result["final_verdict"],
                    "risk_level": council_result["final_risk_level"],
                    "model_output_preview": captured.text_response[:200],
                    "contains_refusal": captured.contains_refusal,
                })

        finally:
            # Always stop the web app server if we started one
            if web_session:
                web_session.stop()

        # Step 5: If no runtime tests succeeded, fall back to static analysis
        if not results and skipped_tests:
            _send_event(job_id, "progress", {
                "stage": "static_analysis",
                "message": "Runtime testing failed — performing static code analysis as fallback...",
                "percent": 85,
            })

            static = analyze_repo_source(
                repo_path=profile.local_path,
                repo_name=profile.name,
                detected_type=profile.detected_type,
            )

            static_results = format_static_analysis_for_council(static, prompts)
            results.extend(static_results)

            # Send static analysis events with actual detailed output
            for i, sr in enumerate(static_results):
                _send_event(job_id, "test_result", {
                    "test_number": i + 1,
                    "category": sr["test_metadata"]["category"],
                    "subcategory": sr["test_metadata"]["subcategory"],
                    "severity": sr["test_metadata"]["severity"],
                    "verdict": sr["final_verdict"],
                    "risk_level": sr["final_risk_level"],
                    "model_output_preview": sr.get("actual_model_output", ""),
                    "contains_refusal": False,
                    "static_analysis": True,
                })

            _send_event(job_id, "progress", {
                "stage": "static_analysis",
                "message": (
                    f"Static analysis complete — found {len(static.get('safety_measures', []))} "
                    f"safety measure(s) and {len(static.get('concerns', []))} concern(s)"
                ),
                "percent": 90,
            })

        # Step 6: Generate reports
        _send_event(job_id, "progress", {
            "stage": "reporting",
            "message": "Generating safety reports...",
            "percent": 92,
        })

        # Save individual reports (skip static results — they have no judge data)
        for r in results:
            if not r.get("static_analysis"):
                report = generate_report(r)
                save_report(report, f"web_{r['input_id']}")

        # Save batch CSV
        csv_path = export_batch_results(results, f"web_{profile.name}")

        # Compute summary — clearly separate evaluated vs skipped
        verdicts = [r["final_verdict"] for r in results]
        risks = [r["final_risk_level"] for r in results]

        static_count = sum(1 for r in results if r.get("static_analysis"))
        runtime_count = len(results) - static_count
        used_static = static_count > 0

        summary = {
            "repo_name": profile.name,
            "repo_url": url,
            "repo_type": profile.detected_type,
            "total_tests_attempted": total,
            "total_tests": len(results),
            "runtime_tests": runtime_count,
            "static_tests": static_count,
            "skipped_count": len(skipped_tests) if not used_static else 0,
            "used_static_analysis": used_static,
            "verdicts": {v: verdicts.count(v) for v in set(verdicts)} if verdicts else {},
            "risks": {r: risks.count(r) for r in set(risks)} if risks else {},
            "pass_rate": _compute_pass_rate(verdicts, used_static),
            "critical_count": risks.count("critical") if risks else 0,
            "human_review_count": sum(1 for r in results if r.get("human_oversight_required")),
            "csv_path": str(csv_path),
        }

        # Compute per-category breakdown
        category_breakdown = {}
        for r in results:
            cat = r.get("test_metadata", {}).get("category", "unknown")
            if cat not in category_breakdown:
                category_breakdown[cat] = {"total": 0, "pass": 0, "fail": 0, "partial": 0}
            category_breakdown[cat]["total"] += 1
            v = r["final_verdict"]
            if v in ("pass", "safe"):
                category_breakdown[cat]["pass"] += 1
            elif used_static and v == "caution":
                # In static mode, caution = "has measures, needs verification"
                category_breakdown[cat]["partial"] += 1
                category_breakdown[cat]["pass"] += 1  # Count as pass for the bar chart
            else:
                category_breakdown[cat]["fail"] += 1

        # Store results in memory and persist to disk
        job_data = {
            "summary": summary,
            "results": results,
            "category_breakdown": category_breakdown,
            "skipped_tests": skipped_tests,
        }
        results_store[job_id] = job_data
        _save_job_results(job_id, job_data)

        _send_event(job_id, "complete", {
            "message": "Evaluation complete",
            "percent": 100,
            "summary": summary,
            "category_breakdown": category_breakdown,
            "skipped_tests": skipped_tests,
        })

    except Exception as e:
        logger.error(f"Evaluation failed: {traceback.format_exc()}")
        _send_event(job_id, "error", {
            "stage": "unknown",
            "message": f"Evaluation failed: {str(e)}",
            "explanation": traceback.format_exc(),
        })


# ---- Routes ----

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/evaluate", methods=["POST"])
def start_evaluation():
    """Start an async evaluation job. Returns job_id for SSE streaming."""
    data = request.get_json()
    url = data.get("url", "").strip()
    full_suite = data.get("full_suite", False)
    domain = data.get("domain", "public_sector")
    env_vars = data.get("env_vars") or {}

    # Sanitize: only allow known safe env var names (letters, digits, underscores)
    import re as _re
    env_vars = {
        k: v for k, v in env_vars.items()
        if isinstance(k, str) and isinstance(v, str)
        and _re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', k)
    }

    if not url:
        return jsonify({"error": "GitHub URL is required"}), 400

    if not url.startswith("https://github.com/"):
        return jsonify({"error": "URL must be a GitHub repository (https://github.com/...)"}), 400

    job_id = f"job_{int(time.time() * 1000)}"
    progress_queues[job_id] = queue.Queue()

    thread = threading.Thread(
        target=_run_evaluation,
        args=(job_id, url, full_suite, domain, env_vars),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def stream_progress(job_id):
    """SSE endpoint for real-time evaluation progress."""
    def generate():
        q = progress_queues.get(job_id)
        if not q:
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'Job not found'}})}\n\n"
            return

        while True:
            try:
                event = q.get(timeout=120)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event") in ("complete", "error"):
                    break
            except queue.Empty:
                # Send heartbeat
                yield f"data: {json.dumps({'event': 'heartbeat', 'data': {}})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/results/<job_id>")
def get_results(job_id):
    """Get full results for a completed evaluation. Checks memory first, then disk."""
    data = results_store.get(job_id)
    if not data:
        # Try loading from persistent storage (survives server restarts)
        data = _load_job_results(job_id)
        if data:
            results_store[job_id] = data  # Re-cache in memory
    if not data:
        return jsonify({"error": "Results not found"}), 404
    return jsonify(data)


@app.route("/api/evaluate/direct", methods=["POST"])
def evaluate_direct():
    """Synchronous evaluation of a prompt-output pair."""
    data = request.get_json()
    prompt = data.get("prompt", "")
    output = data.get("output", "")

    if not prompt or not output:
        return jsonify({"error": "Both prompt and output are required"}), 400

    result = run_council(
        test_prompt=prompt,
        model_output=output,
        metadata={"domain": data.get("domain", "public_sector")},
        input_id="direct_web",
    )

    report = generate_report(result)
    return jsonify({"result": result, "report": report})


@app.route("/api/health")
def health():
    """Check system health."""
    from config.health_check import check_all
    results = check_all(verbose=False)
    status_code = 200 if results["all_pass"] else 503
    return jsonify(results), status_code


if __name__ == "__main__":
    print("\n  UNICC AI Safety Lab — Web Interface")
    print("  http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
