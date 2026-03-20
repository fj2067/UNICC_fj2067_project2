from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any


@dataclass
class JudgeResult:
    judge_name: str
    version: str
    input_id: str
    verdict: str                 # safe | caution | unsafe
    risk_level: str              # low | medium | high | critical
    confidence: float
    scores: Dict[str, int]
    rationale: List[str]
    evidence: List[str]
    flags: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
