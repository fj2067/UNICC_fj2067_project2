"""
Basic unit tests for the UNICC AI Safety Evaluation Lab.

Tests core module imports, data structures, and logic
that don't require Ollama to be running.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImports:
    """Verify all core modules can be imported."""

    def test_config(self):
        from config.settings import (
            LLAMA_GUARD_CATEGORIES,
            VERDICT_PRIORITY,
            RISK_PRIORITY,
        )
        assert len(LLAMA_GUARD_CATEGORIES) == 14
        assert VERDICT_PRIORITY["fail"] > VERDICT_PRIORITY["pass"]

    def test_guardrails(self):
        from guardrails.llama_guard_text import (
            LlamaGuardResult,
            _build_llama_guard_prompt,
            _parse_llama_guard_response,
        )
        from guardrails.llama_guard_vision import VisionGuardResult

    def test_judges(self):
        from judges.base_judge import BaseJudge, JudgeResult
        from judges.security_judge import SecurityJudge
        from judges.ethics_judge import EthicsJudge
        from judges.governance_judge import GovernanceJudge

    def test_council(self):
        from council.orchestrator import run_council
        from council.arbitration import arbitrate

    def test_ingestion(self):
        from ingestion.github_loader import clone_repo, RepoProfile
        from ingestion.sandbox_runner import ExecutionResult
        from ingestion.output_capture import parse_execution_result

    def test_test_generation(self):
        from test_generation.adversarial_prompts import (
            get_all_prompts,
            get_prompt_count_summary,
        )

    def test_reporting(self):
        from reporting.safety_report import generate_report, format_text_report
        from reporting.csv_export import export_batch_results


class TestJudgeResult:
    """Test JudgeResult data structure."""

    def test_creation(self):
        from judges.base_judge import JudgeResult

        result = JudgeResult(
            judge_name="TestJudge",
            version="1.0",
            input_id="test_001",
            verdict="pass",
            risk_level="low",
            confidence=0.85,
            scores={"dimension_a": 1, "dimension_b": 2},
            rationale=["No issues found"],
            evidence=[],
            flags=[],
        )
        assert result.verdict == "pass"
        assert result.risk_level == "low"

    def test_to_dict(self):
        from judges.base_judge import JudgeResult

        result = JudgeResult(
            judge_name="TestJudge",
            version="1.0",
            input_id="test_001",
            verdict="unsafe",
            risk_level="critical",
            confidence=0.90,
        )
        d = result.to_dict()
        assert d["verdict"] == "unsafe"
        assert d["risk_level"] == "critical"
        assert isinstance(d, dict)


class TestLlamaGuardParsing:
    """Test Llama Guard response parsing (offline, no model needed)."""

    def test_parse_safe(self):
        from guardrails.llama_guard_text import _parse_llama_guard_response

        result = _parse_llama_guard_response("safe")
        assert result.is_safe is True
        assert result.violated_categories == []

    def test_parse_unsafe_single(self):
        from guardrails.llama_guard_text import _parse_llama_guard_response

        result = _parse_llama_guard_response("unsafe\nS1")
        assert result.is_safe is False
        assert "S1" in result.violated_categories
        assert result.has_critical_violation is True

    def test_parse_unsafe_multiple(self):
        from guardrails.llama_guard_text import _parse_llama_guard_response

        result = _parse_llama_guard_response("unsafe\nS7, S10")
        assert result.is_safe is False
        assert "S7" in result.violated_categories
        assert "S10" in result.violated_categories
        assert result.has_critical_violation is False  # S7 and S10 not in CRITICAL

    def test_parse_empty(self):
        from guardrails.llama_guard_text import _parse_llama_guard_response

        result = _parse_llama_guard_response("")
        assert result.is_safe is False
        assert result.error is not None

    def test_build_prompt(self):
        from guardrails.llama_guard_text import _build_llama_guard_prompt

        prompt = _build_llama_guard_prompt("Hello", "Hi there!")
        assert "User: Hello" in prompt
        assert "Agent: Hi there!" in prompt
        assert "UNSAFE CONTENT CATEGORIES" in prompt


class TestAdversarialPrompts:
    """Test the adversarial prompt library."""

    def test_all_prompts_have_required_fields(self):
        from test_generation.adversarial_prompts import get_all_prompts

        prompts = get_all_prompts()
        assert len(prompts) > 20

        for p in prompts:
            assert p.prompt, f"Empty prompt in {p.subcategory}"
            assert p.category, f"Missing category in {p.subcategory}"
            assert p.severity in ("critical", "high", "medium", "low")
            assert p.expected_safe_behavior

    def test_critical_prompts_exist(self):
        from test_generation.adversarial_prompts import get_critical_prompts

        critical = get_critical_prompts()
        assert len(critical) >= 5

    def test_prompt_count_summary(self):
        from test_generation.adversarial_prompts import get_prompt_count_summary

        summary = get_prompt_count_summary()
        assert "prompt_injection" in summary
        assert "safe_baseline" in summary
        assert summary["safe_baseline"]["total"] >= 3

    def test_model_type_filtering(self):
        from test_generation.adversarial_prompts import (
            get_prompts_for_model_type,
            get_all_prompts,
        )

        all_count = len(get_all_prompts())
        classifier_count = len(get_prompts_for_model_type("classifier"))
        assert classifier_count < all_count


class TestOutputCapture:
    """Test output capture and parsing."""

    def test_refusal_detection(self):
        from ingestion.output_capture import _detect_refusal

        assert _detect_refusal("I can't help with that request") is True
        assert _detect_refusal("I'm unable to provide that information") is True
        assert _detect_refusal("Here is the information you requested") is False

    def test_json_extraction(self):
        from ingestion.output_capture import _try_extract_json

        assert _try_extract_json('{"result": "ok"}') == {"result": "ok"}
        assert _try_extract_json('Some text {"result": "ok"} more text') == {"result": "ok"}
        assert _try_extract_json("no json here") is None

    def test_text_from_json(self):
        from ingestion.output_capture import _extract_text_from_json

        assert _extract_text_from_json({"response": "hello"}) == "hello"
        assert _extract_text_from_json({"output": "world"}) == "world"
        assert _extract_text_from_json({"messages": [{"role": "assistant", "content": "hi"}]}) == "hi"


class TestArbitration:
    """Test council arbitration logic."""

    def test_conservative_resolution(self):
        from council.arbitration import arbitrate
        from judges.base_judge import JudgeResult

        safe_result = JudgeResult(
            judge_name="Judge1", version="1.0", input_id="t1",
            verdict="pass", risk_level="low", confidence=0.8,
            scores={"dim_a": 1},
        )
        unsafe_result = JudgeResult(
            judge_name="Judge2", version="1.0", input_id="t1",
            verdict="unsafe", risk_level="high", confidence=0.9,
            scores={"dim_a": 5},
        )
        neutral_result = JudgeResult(
            judge_name="Judge3", version="1.0", input_id="t1",
            verdict="caution", risk_level="medium", confidence=0.7,
            scores={"dim_a": 3},
        )

        arb = arbitrate(safe_result, unsafe_result, neutral_result)
        # Conservative: should take the strictest
        assert arb["final_verdict"] == "unsafe"
        assert arb["final_risk_level"] == "high"
        assert arb["resolution_strategy"] == "conservative_strictest_wins"


class TestRepoProfile:
    """Test repository profiling."""

    def test_profile_creation(self):
        from ingestion.github_loader import RepoProfile

        profile = RepoProfile(
            url="https://github.com/test/repo",
            local_path="/tmp/test",
            name="test_repo",
        )
        d = profile.to_dict()
        assert d["name"] == "test_repo"
        assert d["language"] == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
