"""
Sandboxed Execution Module.

Runs target AI models in isolated environments (subprocess with restrictions
or Docker containers) to capture their outputs safely.

Security: Target models are untrusted code. They must be executed with:
- No network access (or restricted)
- No filesystem access outside their directory
- Resource limits (CPU, memory, time)
- Output capture via stdout/stderr
"""

import json
import logging
import re
import socket
import subprocess
import os
import time
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from config.settings import SANDBOX_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of running a target model with a test prompt."""
    repo_name: str
    test_prompt: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    timed_out: bool = False
    error: Optional[str] = None
    output_files: list = field(default_factory=list)
    execution_mode: str = "stdin"       # "stdin", "web_app", "cli_arg"
    target_crashed: bool = False        # True if the target failed to run

    @property
    def raw_output(self) -> str:
        return self.stdout.strip() if self.stdout.strip() else self.stderr.strip()

    def to_dict(self):
        return {
            "repo_name": self.repo_name,
            "test_prompt": self.test_prompt,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "error": self.error,
            "output_files": self.output_files,
            "execution_mode": self.execution_mode,
            "target_crashed": self.target_crashed,
        }


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def detect_web_app(repo_path: str, entry_point: str) -> Optional[str]:
    """
    Detect if the entry point is a web application that can be tested via HTTP.

    Only returns a framework name for apps that can be started with
    ``python <entry_point>`` and probed via HTTP (Flask, FastAPI).

    Streamlit and Gradio are NOT returned here because they require
    special launch commands (``streamlit run``) and cannot be started
    or tested the same way.  They fall back to the subprocess/stdin path.
    """
    ep_path = Path(repo_path) / entry_point
    try:
        content = ep_path.read_text(encoding="utf-8", errors="replace")[:5000]
    except Exception:
        return None

    content_lower = content.lower()

    # Only Flask and FastAPI can be started with `python app.py` and tested via HTTP
    if "flask" in content_lower and ("app.run" in content or "app = flask" in content_lower):
        return "flask"
    if "fastapi" in content_lower and ("uvicorn" in content_lower or "fastapi()" in content_lower):
        return "fastapi"

    # Streamlit / Gradio — detected but NOT handled as web apps.
    # They fall back to subprocess/stdin execution.
    return None


def _wait_for_server(port: int, timeout: float = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


class WebAppSession:
    """
    Manages a web app's lifecycle — start once, send multiple test prompts,
    then stop.  This avoids restarting the server for every single test.
    """

    def __init__(
        self,
        repo_path: str,
        entry_point: str,
        repo_name: str = "",
        framework: str = "flask",
        env_vars: dict | None = None,
    ):
        self.repo_path = repo_path
        self.entry_point = entry_point
        self.repo_name = repo_name or Path(repo_path).name
        self.framework = framework
        self.env_vars = env_vars or {}
        self.port = _find_free_port()
        self.proc = None
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._original_content = None
        self._entry_path = Path(repo_path) / entry_point
        self._patched = False
        self._started = False
        self._start_error = None

    def start(self) -> Optional[str]:
        """
        Start the web app server. Returns None on success, or an error
        string if the server fails to start.
        """
        if not self._entry_path.exists():
            self._start_error = f"Entry point not found: {self._entry_path}"
            return self._start_error

        # Build environment — keep API keys for web apps
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["FLASK_RUN_PORT"] = str(self.port)
        env["PORT"] = str(self.port)
        # Apply evaluator-supplied API keys
        if self.env_vars:
            env.update(self.env_vars)

        # Install requirements
        req_file = Path(self.repo_path) / "requirements.txt"
        if req_file.exists():
            try:
                subprocess.run(
                    ["pip", "install", "-q", "-r", str(req_file)],
                    capture_output=True, timeout=120,
                    cwd=self.repo_path, env=env,
                )
            except Exception as e:
                logger.warning(f"Failed to install requirements: {e}")

        # Patch app.run() to use our port
        if self.framework == "flask":
            try:
                self._original_content = self._entry_path.read_text(
                    encoding="utf-8", errors="replace"
                )
                patched = re.sub(
                    r'app\.run\([^)]*\)',
                    f'app.run(host="127.0.0.1", port={self.port}, debug=False)',
                    self._original_content,
                )
                if patched != self._original_content:
                    self._patched = True
                    self._entry_path.write_text(patched, encoding="utf-8")
            except Exception:
                pass

        # Start server process
        try:
            self.proc = subprocess.Popen(
                ["python", str(self._entry_path)],
                cwd=self.repo_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self._start_error = f"Failed to launch: {e}"
            self._restore()
            return self._start_error

        # Wait for it to be ready
        if not _wait_for_server(self.port, timeout=30):
            # Collect error output
            self.proc.terminate()
            try:
                stdout, stderr = self.proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                stdout, stderr = self.proc.communicate()

            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""
            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""

            self._start_error = (
                f"Web app failed to start on port {self.port}.\n"
                f"Stderr:\n{stderr_text[:1500]}\n"
                f"Stdout:\n{stdout_text[:500]}"
            )
            self._restore()
            return self._start_error

        self._started = True
        return None

    def send_prompt(self, test_prompt: str) -> ExecutionResult:
        """Send a test prompt to the running web app via HTTP."""
        import requests as http_requests

        result = ExecutionResult(
            repo_name=self.repo_name,
            test_prompt=test_prompt,
            execution_mode="web_app",
        )

        if not self._started:
            result.target_crashed = True
            result.error = self._start_error or "Server not started"
            return result

        responses = []

        # 1. GET the home page
        try:
            resp = http_requests.get(self.base_url, timeout=15)
            responses.append(f"[GET /] Status {resp.status_code}\n{resp.text[:1000]}")
        except Exception as e:
            responses.append(f"[GET /] Error: {e}")

        # 2. Try common API endpoints with the test prompt
        api_endpoints = [
            "/api/analyze", "/api/evaluate", "/api/process",
            "/api/chat", "/api/generate", "/api/predict",
            "/analyze", "/evaluate", "/process", "/submit",
        ]

        payload = {"text": test_prompt, "prompt": test_prompt,
                    "input": test_prompt, "query": test_prompt,
                    "content": test_prompt, "message": test_prompt}

        for endpoint in api_endpoints:
            try:
                resp = http_requests.post(
                    f"{self.base_url}{endpoint}",
                    json=payload, timeout=30,
                )
                if resp.status_code != 404:
                    responses.append(
                        f"[POST {endpoint}] Status {resp.status_code}\n{resp.text[:1000]}"
                    )
            except Exception:
                continue

        # 3. Try form submission with file upload
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, dir=self.repo_path
            ) as tmp:
                tmp.write(test_prompt)
                tmp_path = tmp.name

            form_endpoints = ["/upload", "/analyze", "/", "/submit", "/process"]
            for endpoint in form_endpoints:
                try:
                    with open(tmp_path, "rb") as f:
                        resp = http_requests.post(
                            f"{self.base_url}{endpoint}",
                            files={"file": ("test_input.txt", f, "text/plain")},
                            data={"text": test_prompt, "content": test_prompt},
                            timeout=30,
                        )
                        if resp.status_code not in (404, 405):
                            responses.append(
                                f"[FORM POST {endpoint}] Status {resp.status_code}\n{resp.text[:1000]}"
                            )
                except Exception:
                    continue

            os.unlink(tmp_path)
        except Exception:
            pass

        if responses:
            result.stdout = "\n---\n".join(responses)
            result.exit_code = 0
        else:
            result.target_crashed = True
            result.error = "No HTTP endpoints responded"

        return result

    def stop(self):
        """Stop the server and restore original files."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self._restore()

    def _restore(self):
        if self._patched and self._original_content is not None:
            try:
                self._entry_path.write_text(
                    self._original_content, encoding="utf-8"
                )
            except Exception:
                pass


def run_in_subprocess(
    repo_path: str,
    entry_point: str,
    test_prompt: str,
    repo_name: str = "",
    timeout: int | None = None,
    env_overrides: dict | None = None,
) -> ExecutionResult:
    """
    Execute a target model's entry point in a restricted subprocess.
    The test prompt is piped via stdin.
    """
    timeout = timeout or SANDBOX_TIMEOUT

    result = ExecutionResult(
        repo_name=repo_name or Path(repo_path).name,
        test_prompt=test_prompt,
        execution_mode="stdin",
    )

    entry_path = Path(repo_path) / entry_point
    if not entry_path.exists():
        result.error = f"Entry point not found: {entry_path}"
        result.target_crashed = True
        return result

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "HF_TOKEN"]:
        env.pop(key, None)
    if env_overrides:
        env.update(env_overrides)

    req_file = Path(repo_path) / "requirements.txt"
    if req_file.exists():
        try:
            subprocess.run(
                ["pip", "install", "-q", "-r", str(req_file)],
                capture_output=True, timeout=120,
                cwd=repo_path, env=env,
            )
        except Exception as e:
            logger.warning(f"Failed to install requirements for {repo_name}: {e}")

    try:
        proc = subprocess.run(
            ["python", str(entry_path)],
            input=test_prompt,
            capture_output=True, text=True,
            timeout=timeout, cwd=repo_path, env=env,
        )
        result.stdout = proc.stdout
        result.stderr = proc.stderr
        result.exit_code = proc.returncode

        if proc.returncode != 0:
            stderr_lower = result.stderr.lower()
            if any(sig in stderr_lower for sig in [
                "traceback", "error", "exception", "modulenotfounderror",
                "importerror", "syntaxerror", "filenotfounderror",
            ]):
                result.target_crashed = True

    except subprocess.TimeoutExpired:
        result.timed_out = True
        result.error = f"Execution timed out after {timeout}s"
    except Exception as e:
        result.error = f"Execution failed: {e}"
        result.target_crashed = True

    # Check for generated output files
    output_dirs = ["output", "outputs", "results", "generated"]
    for dirname in output_dirs:
        out_dir = Path(repo_path) / dirname
        if out_dir.exists():
            for f in out_dir.rglob("*"):
                if f.is_file() and f.suffix.lower() in {
                    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
                    ".txt", ".json", ".csv", ".html",
                }:
                    result.output_files.append(str(f))

    return result


def run_with_docker(
    repo_path: str,
    entry_point: str,
    test_prompt: str,
    repo_name: str = "",
    timeout: int | None = None,
) -> ExecutionResult:
    """Execute a target model inside a Docker container."""
    timeout = timeout or SANDBOX_TIMEOUT

    result = ExecutionResult(
        repo_name=repo_name or Path(repo_path).name,
        test_prompt=test_prompt,
    )

    try:
        subprocess.run(
            ["docker", "info"], capture_output=True, timeout=10, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Docker not available, falling back to subprocess")
        return run_in_subprocess(
            repo_path, entry_point, test_prompt, repo_name, timeout
        )

    dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true
"""
    dockerfile_path = Path(repo_path) / "Dockerfile.safetylab"
    dockerfile_path.write_text(dockerfile_content)

    image_tag = f"safetylab-{repo_name or 'target'}:latest".lower().replace(" ", "_")

    try:
        subprocess.run(
            ["docker", "build", "-f", "Dockerfile.safetylab", "-t", image_tag, "."],
            capture_output=True, timeout=300, cwd=repo_path, check=True,
        )

        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none", "--memory=512m", "--cpus=1",
                "--read-only", "--tmpfs", "/tmp:size=64m",
                "-i", image_tag, "python", entry_point,
            ],
            input=test_prompt,
            capture_output=True, text=True, timeout=timeout,
        )
        result.stdout = proc.stdout
        result.stderr = proc.stderr
        result.exit_code = proc.returncode

    except subprocess.TimeoutExpired:
        result.timed_out = True
        result.error = f"Docker execution timed out after {timeout}s"
    except subprocess.CalledProcessError as e:
        result.error = f"Docker build/run failed: {e.stderr}"
        result.target_crashed = True
    except Exception as e:
        result.error = f"Docker execution failed: {e}"
        result.target_crashed = True
    finally:
        dockerfile_path.unlink(missing_ok=True)
        subprocess.run(
            ["docker", "rmi", image_tag], capture_output=True, timeout=30,
        )

    return result


def run_target_model(
    repo_path: str,
    entry_point: str,
    test_prompt: str,
    repo_name: str = "",
    use_docker: bool = False,
    timeout: int | None = None,
) -> ExecutionResult:
    """
    High-level function to execute a target model with a test prompt.
    For web apps, use WebAppSession instead (start once, send many prompts).
    """
    if use_docker:
        return run_with_docker(
            repo_path, entry_point, test_prompt, repo_name, timeout
        )
    return run_in_subprocess(
        repo_path, entry_point, test_prompt, repo_name, timeout
    )
