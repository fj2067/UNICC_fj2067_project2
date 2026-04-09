"""
GitHub Repository Ingestion Module.

Accepts GitHub repository URLs, clones them into isolated directories,
detects the project type (Python/Node/etc.), identifies entry points,
and prepares them for sandboxed execution.
"""

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from config.settings import CLONED_REPOS_DIR

logger = logging.getLogger(__name__)


@dataclass
class RepoProfile:
    """Profile of a cloned repository, describing its structure and entry points."""
    url: str
    local_path: str
    name: str
    cohort: str = ""
    language: str = "unknown"
    entry_points: list = field(default_factory=list)
    has_requirements: bool = False
    has_dockerfile: bool = False
    has_package_json: bool = False
    readme_summary: str = ""
    detected_type: str = "unknown"  # "chatbot", "content_gen", "agent", "classifier", etc.
    python_files: list = field(default_factory=list)
    error: Optional[str] = None
    run_command: str = ""

    def to_dict(self):
        return {
            "url": self.url,
            "local_path": self.local_path,
            "name": self.name,
            "cohort": self.cohort,
            "language": self.language,
            "entry_points": self.entry_points,
            "detected_type": self.detected_type,
            "has_requirements": self.has_requirements,
            "has_dockerfile": self.has_dockerfile,
            "python_files": self.python_files,
            "error": self.error,
            "run_command": self.run_command,
        }


def clone_repo(url: str, name: str = "", cohort: str = "") -> RepoProfile:
    """
    Clone a GitHub repository and profile its structure.

    Args:
        url: GitHub repository URL (HTTPS).
        name: Human-readable name for this project.
        cohort: Which cohort this belongs to (fall_2024, spring_2025).

    Returns:
        RepoProfile with detected structure and entry points.
    """
    if not name:
        name = url.rstrip("/").split("/")[-1].replace(".git", "")

    dest = CLONED_REPOS_DIR / f"{cohort}_{name}" if cohort else CLONED_REPOS_DIR / name

    # Clean previous clone if exists
    # On Windows, .git files are read-only and need permission override to delete
    if dest.exists():
        import time
        import stat

        def _force_remove(func, path, exc_info):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except PermissionError:
                pass

        deleted = False
        for attempt in range(3):
            try:
                shutil.rmtree(dest, onerror=_force_remove)
                deleted = True
                break
            except PermissionError:
                time.sleep(1)

        if not deleted:
            # Directory is locked by another process — clone to a
            # unique path instead of failing.
            dest = CLONED_REPOS_DIR / f"{name}_{int(time.time())}"
            logger.warning(
                f"Previous clone is locked, using fresh path: {dest}"
            )

    profile = RepoProfile(
        url=url, local_path=str(dest), name=name, cohort=cohort
    )

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # A non-zero exit code with a valid .git directory means the clone
        # succeeded but checkout failed for some files (e.g. filenames with
        # characters invalid on Windows like " or :).  The repo is still
        # usable, so treat this as a warning rather than an error.
        if result.returncode != 0:
            if (dest / ".git").exists():
                logger.warning(
                    f"Clone succeeded with partial checkout — some files "
                    f"could not be checked out (likely invalid filenames "
                    f"on Windows): {result.stderr.strip()}"
                )
                # Git aborts the entire checkout when it hits an invalid
                # path on Windows.  Force-checkout everything it can.
                subprocess.run(
                    ["git", "checkout", "HEAD", "--", "."],
                    cwd=str(dest),
                    capture_output=True,
                    text=True,
                )
            else:
                profile.error = f"Git clone failed: {result.stderr.strip()}"
                return profile
    except subprocess.TimeoutExpired:
        profile.error = "Git clone timed out after 120 seconds"
        return profile
    except FileNotFoundError:
        profile.error = "git is not installed or not in PATH"
        return profile

    _analyze_repo(profile, dest)
    return profile


def _analyze_repo(profile: RepoProfile, repo_dir: Path):
    """Analyze the cloned repo to detect language, entry points, and type."""

    # Detect Python files
    py_files = sorted(repo_dir.rglob("*.py"))
    profile.python_files = [str(f.relative_to(repo_dir)) for f in py_files]

    # Detect Node files
    js_files = list(repo_dir.rglob("*.js")) + list(repo_dir.rglob("*.ts"))

    # Determine primary language
    if len(py_files) >= len(js_files):
        profile.language = "python"
    elif js_files:
        profile.language = "javascript"

    # Check for dependency/config files
    profile.has_requirements = (repo_dir / "requirements.txt").exists()
    profile.has_dockerfile = (repo_dir / "Dockerfile").exists()
    profile.has_package_json = (repo_dir / "package.json").exists()

    # Detect entry points
    entry_candidates = [
        "main.py", "app.py", "api.py", "run.py", "server.py", "index.py",
        "demo.py", "cli.py", "start.py", "launch.py", "evaluate.py",
    ]
    for candidate in entry_candidates:
        if (repo_dir / candidate).exists():
            profile.entry_points.append(candidate)

    # If no standard entry point found, use any top-level .py file
    if not profile.entry_points:
        for py_file in sorted(repo_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            profile.entry_points.append(py_file.name)

    # Also check for __main__.py in subdirectories
    for main_file in repo_dir.rglob("__main__.py"):
        rel = str(main_file.relative_to(repo_dir))
        if rel not in profile.entry_points:
            profile.entry_points.append(rel)

    # Detect Streamlit apps by reading entry point contents
    for ep in profile.entry_points:
        ep_path = repo_dir / ep
        try:
            content = ep_path.read_text(encoding="utf-8", errors="replace")[:3000]
            if "streamlit" in content.lower():
                profile.detected_type = "web_app"
                profile.run_command = f"streamlit run {ep}"
                break
        except Exception:
            continue

    # Read README for project type hints
    for readme_name in ["README.md", "readme.md", "README.txt", "README"]:
        readme_path = repo_dir / readme_name
        if readme_path.exists():
            try:
                text = readme_path.read_text(encoding="utf-8", errors="replace")[:2000]
                profile.readme_summary = text
                _detect_project_type(profile, text)
            except Exception:
                pass
            break

    if profile.detected_type == "unknown":
        _detect_project_type_from_code(profile, repo_dir)


def _detect_project_type(profile: RepoProfile, readme_text: str):
    """Infer what kind of AI project this is from README content."""
    text_lower = readme_text.lower()

    type_signals = {
        "chatbot": ["chatbot", "chat bot", "conversational", "dialogue"],
        "content_gen": ["content generat", "text generat", "image generat", "story generat"],
        "agent": ["agent", "agentic", "tool use", "autonomous"],
        "classifier": ["classif", "sentiment", "categoriz", "xenophob", "analys"],
        "summarizer": ["summar", "abstract"],
        "translator": ["translat", "multilingual"],
        "rag": ["retrieval", "rag", "knowledge base", "vector"],
        "web_app": ["streamlit", "gradio", "flask", "fastapi", "django"],
        "safety_tool": ["safety", "moderat", "guard", "filter", "detect"],
    }

    for project_type, signals in type_signals.items():
        if any(signal in text_lower for signal in signals):
            profile.detected_type = project_type
            return


def _detect_project_type_from_code(profile: RepoProfile, repo_dir: Path):
    """Infer project type from code imports and patterns."""
    all_code = ""
    for py_file in list(repo_dir.rglob("*.py"))[:10]:  # Sample first 10 files
        try:
            all_code += py_file.read_text(encoding="utf-8", errors="replace")[:1000]
        except Exception:
            continue

    code_lower = all_code.lower()

    if "streamlit" in code_lower or "gradio" in code_lower or "flask" in code_lower:
        profile.detected_type = "web_app"
    elif "openai" in code_lower or "anthropic" in code_lower or "ollama" in code_lower:
        profile.detected_type = "llm_app"
    elif "langchain" in code_lower or "llamaindex" in code_lower:
        profile.detected_type = "rag"
    elif "torch" in code_lower or "tensorflow" in code_lower:
        profile.detected_type = "ml_model"


def clone_multiple(repo_list: list[dict]) -> list[RepoProfile]:
    """
    Clone multiple repos from a list of dicts with keys: url, name, cohort.
    """
    profiles = []
    for repo_info in repo_list:
        profile = clone_repo(
            url=repo_info["url"],
            name=repo_info.get("name", ""),
            cohort=repo_info.get("cohort", ""),
        )
        profiles.append(profile)
        if profile.error:
            logger.error(f"Failed to clone {repo_info['url']}: {profile.error}")
        else:
            logger.info(
                f"Cloned {profile.name}: {profile.language}, "
                f"type={profile.detected_type}, "
                f"entry_points={profile.entry_points}"
            )
    return profiles
