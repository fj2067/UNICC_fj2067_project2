"""
Basic tests for UNICC AI Safety Council
These confirm the core modules load and run without crashing.
"""
import sys
import os

# Add the root directory to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all core modules can be imported."""
    from judges.technical_judge import SecurityJudge
    from judges.governance_judge import GovernanceJudge
    from judges.ethics_judge import EthicsJudge
    from council.moe_council import SafetyCouncil
    from council.arbitration import council_decision
    from output.report import generate_report
    assert True


def test_judges_instantiate():
    """Test that all three judges can be created."""
    from judges.technical_judge import SecurityJudge
    from judges.governance_judge import GovernanceJudge
    from judges.ethics_judge import EthicsJudge

    j1 = SecurityJudge()
    j2 = GovernanceJudge()
    j3 = EthicsJudge()

    assert j1 is not None
    assert j2 is not None
    assert j3 is not None


def test_council_instantiates():
    """Test that the council can be created with all three judges."""
    from judges.technical_judge import SecurityJudge
    from judges.governance_judge import GovernanceJudge
    from judges.ethics_judge import EthicsJudge
    from council.moe_council import SafetyCouncil

    judges = [SecurityJudge(), GovernanceJudge(), EthicsJudge()]
    council = SafetyCouncil(judges)

    assert council is not None


def test_evaluation_runs():
    """Test that a full evaluation produces a result."""
    from judges.technical_judge import SecurityJudge
    from judges.governance_judge import GovernanceJudge
    from judges.ethics_judge import EthicsJudge
    from council.moe_council import SafetyCouncil
    from council.arbitration import council_decision
    from output.report import generate_report

    sample_text = "This AI agent answers questions about UN humanitarian policy."

    judges = [SecurityJudge(), GovernanceJudge(), EthicsJudge()]
    council = SafetyCouncil(judges)
    results = council.evaluate(sample_text)
    decision = council_decision(results)
    report = generate_report(sample_text, results, decision)

    # Report must exist and not be empty
    assert report is not None
    assert len(str(report)) > 0


def test_arbitration_produces_decision():
    """Test that arbitration returns a valid decision."""
    from council.arbitration import council_decision

    # Simulate what three judges might return
    mock_results = [
        {"judge": "security", "score": 0.8, "verdict": "safe"},
        {"judge": "governance", "score": 0.7, "verdict": "safe"},
        {"judge": "ethics", "score": 0.9, "verdict": "safe"},
    ]

    decision = council_decision(mock_results)

    # Decision must exist
    assert decision is not None
