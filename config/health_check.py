"""
System Health Check and Diagnostics.

Run this before any evaluation to verify:
- Ollama is running and reachable
- Required models are pulled and loadable
- GPU memory is sufficient
- All Python dependencies are installed

Usage:
    python -m config.health_check
"""

import importlib
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import requests

from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_GENERATE_URL,
    LLAMA_GUARD_MODEL,
    LLAMA_GUARD_VISION_MODEL,
    REASONING_MODEL,
    OLLAMA_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_all(verbose: bool = True) -> dict:
    """
    Run all health checks and return a structured status report.

    Returns:
        Dict with check results and overall pass/fail.
    """
    results = {}
    all_pass = True

    checks = [
        ("python_deps", check_python_dependencies),
        ("ollama_running", check_ollama_running),
        ("ollama_models", check_ollama_models),
        ("model_inference", check_model_inference),
        ("git_available", check_git_available),
        ("disk_space", check_disk_space),
    ]

    for name, check_fn in checks:
        try:
            result = check_fn()
            results[name] = result
            if not result.get("ok"):
                all_pass = False
            if verbose:
                status = f"{GREEN}PASS{RESET}" if result["ok"] else f"{RED}FAIL{RESET}"
                print(f"  [{status}] {name}: {result.get('message', '')}")
                if not result["ok"] and result.get("fix"):
                    print(f"         {YELLOW}Fix: {result['fix']}{RESET}")
        except Exception as e:
            results[name] = {"ok": False, "message": str(e)}
            all_pass = False
            if verbose:
                print(f"  [{RED}FAIL{RESET}] {name}: {e}")

    results["all_pass"] = all_pass

    if verbose:
        print()
        if all_pass:
            print(f"  {GREEN}{BOLD}All checks passed. System ready.{RESET}")
        else:
            print(f"  {RED}{BOLD}Some checks failed. See fixes above.{RESET}")

    return results


def check_python_dependencies() -> dict:
    """Check that all required Python packages are installed."""
    required = {
        "requests": "requests",
        "yaml": "pyyaml",
        "PIL": "Pillow",
        "pandas": "pandas",
        "jinja2": "jinja2",
        "flask": "flask",
    }
    missing = []
    for module_name, pip_name in required.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        return {
            "ok": False,
            "message": f"Missing packages: {', '.join(missing)}",
            "fix": f"pip install {' '.join(missing)}",
            "missing": missing,
        }
    return {"ok": True, "message": "All dependencies installed"}


def check_ollama_running() -> dict:
    """Check if Ollama server is running and reachable."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return {
            "ok": True,
            "message": f"Ollama running at {OLLAMA_BASE_URL} ({len(models)} models loaded)",
            "models_available": [m["name"] for m in models],
        }
    except requests.ConnectionError:
        return {
            "ok": False,
            "message": f"Ollama not reachable at {OLLAMA_BASE_URL}",
            "fix": (
                "Start Ollama with: ollama serve\n"
                "         Or set OLLAMA_BASE_URL env var if using a different port.\n"
                "         On DGX: Check if Ollama is installed. If not:\n"
                "           curl -fsSL https://ollama.com/install.sh | sh\n"
                "           OLLAMA_HOST=0.0.0.0:11434 ollama serve &"
            ),
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Ollama check failed: {e}",
            "fix": "Ensure Ollama is running: ollama serve",
        }


def check_ollama_models() -> dict:
    """Check if required models are pulled."""
    required_models = [LLAMA_GUARD_MODEL, REASONING_MODEL]
    optional_models = [LLAMA_GUARD_VISION_MODEL]

    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        available = {m["name"] for m in resp.json().get("models", [])}
        # Ollama sometimes uses short names vs full names
        available_short = {n.split(":")[0] for n in available}

        missing_required = []
        for model in required_models:
            short = model.split(":")[0]
            if model not in available and short not in available_short:
                missing_required.append(model)

        missing_optional = []
        for model in optional_models:
            short = model.split(":")[0]
            if model not in available and short not in available_short:
                missing_optional.append(model)

        if missing_required:
            pull_cmds = " && ".join(f"ollama pull {m}" for m in missing_required)
            return {
                "ok": False,
                "message": f"Missing required models: {', '.join(missing_required)}",
                "fix": pull_cmds,
                "available": list(available),
            }

        msg = f"Required models available: {', '.join(required_models)}"
        if missing_optional:
            msg += f" (optional missing: {', '.join(missing_optional)})"

        return {
            "ok": True,
            "message": msg,
            "available": list(available),
            "missing_optional": missing_optional,
        }

    except requests.ConnectionError:
        return {
            "ok": False,
            "message": "Cannot check models — Ollama not running",
            "fix": "Start Ollama first: ollama serve",
        }


def check_model_inference() -> dict:
    """Test that the reasoning model can actually generate output."""
    try:
        start = time.time()
        resp = requests.post(
            OLLAMA_GENERATE_URL,
            json={
                "model": REASONING_MODEL,
                "prompt": "Reply with exactly one word: hello",
                "stream": False,
                "options": {"num_predict": 10, "temperature": 0},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        elapsed = time.time() - start
        resp.raise_for_status()
        output = resp.json().get("response", "").strip()

        if not output:
            return {
                "ok": False,
                "message": f"Model responded but output was empty (took {elapsed:.1f}s)",
                "fix": f"Model may be corrupted. Try: ollama rm {REASONING_MODEL} && ollama pull {REASONING_MODEL}",
            }

        return {
            "ok": True,
            "message": f"Inference OK ({elapsed:.1f}s, output: '{output[:30]}')",
            "latency_seconds": round(elapsed, 2),
        }

    except requests.Timeout:
        return {
            "ok": False,
            "message": f"Model inference timed out after {OLLAMA_TIMEOUT}s",
            "fix": (
                "Likely causes:\n"
                "         1. First run — model loading into GPU takes 30-60s. Try again.\n"
                "         2. Insufficient GPU memory. Check with: nvidia-smi\n"
                "         3. Another process using the GPU. Kill competing processes.\n"
                f"         4. Increase timeout: set OLLAMA_TIMEOUT=300"
            ),
        }
    except requests.ConnectionError:
        return {
            "ok": False,
            "message": "Cannot test inference — Ollama not running",
            "fix": "Start Ollama first",
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Inference failed: {e}",
            "fix": "Check Ollama logs: journalctl -u ollama or ollama logs",
        }


def check_git_available() -> dict:
    """Check if git is installed (needed for repo cloning)."""
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        )
        return {
            "ok": True,
            "message": result.stdout.strip(),
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "message": "git not found in PATH",
            "fix": "Install git: apt install git (Linux) or download from git-scm.com",
        }


def check_disk_space() -> dict:
    """Check available disk space (models need several GB)."""
    import shutil

    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024 ** 3)

    if free_gb < 5:
        return {
            "ok": False,
            "message": f"Low disk space: {free_gb:.1f} GB free",
            "fix": "Need at least 5 GB free for model weights. Clean up or expand storage.",
        }
    return {
        "ok": True,
        "message": f"{free_gb:.1f} GB free",
    }


if __name__ == "__main__":
    print(f"\n{BOLD}UNICC AI Safety Lab — System Health Check{RESET}\n")
    results = check_all(verbose=True)
    print()
    sys.exit(0 if results["all_pass"] else 1)
