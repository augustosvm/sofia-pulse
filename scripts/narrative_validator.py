# scripts/narrative_validator.py
"""
Narrative Validator for Sofia Insight Engine
Anti-zero + Anti-hallucination + "Does this change decisions?"
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

# Zero string patterns (PT-BR and EN-US formats)
ZERO_STR_PATTERNS = [
    r"\b0%\b", r"\b0,0%\b", r"\b0\.0%\b",
    r"\bUS\$\s*0\b", r"\b\$0\b", r"\bR\$\s*0\b",
    r"\b0\s+eventos\b", r"\b0\s+vagas\b", r"\b0\s+papers\b",
    r"\b0\s+deals\b", r"\b0\s+fatalidades\b",
]

# Hyperbole patterns that indicate ungrounded claims
HYPERBOLE_PATTERNS = [
    r"\b(inevitável|garantido|com certeza|sem dúvida)\b",
    r"\b(maior da década|maior da história|nunca visto)\b",
    r"\b(unprecedented|guaranteed|inevitable|certainly)\b",
    r"\b(always|never|every single|all of)\b",
]

# Numeric extraction regex
NUM_RE = re.compile(r"(?<![A-Za-z])(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)(?![A-Za-z])")


@dataclass
class ValidationResult:
    passed: bool
    reasons: List[str]
    flags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pass": self.passed,
            "reasons": self.reasons,
            "flags": self.flags
        }


def _flatten_metric_values(evidence: List[Dict[str, Any]]) -> List[Any]:
    """Extract all values from evidence list"""
    out = []
    for e in evidence or []:
        val = e.get("value")
        if val is not None:
            out.append(val)
    return out


def _contains_zero_strings(text: str) -> bool:
    """Check if text contains zero-value strings that indicate missing data"""
    t = (text or "").lower()
    return any(re.search(p, t, re.IGNORECASE) for p in ZERO_STR_PATTERNS)


def _contains_hyperbole(text: str) -> bool:
    """Check if text contains hyperbolic/ungrounded claims"""
    t = (text or "").lower()
    return any(re.search(p, t, re.IGNORECASE) for p in HYPERBOLE_PATTERNS)


def _extract_numbers(text: str) -> List[str]:
    """Extract all numeric strings from text"""
    return [m.group(1) for m in NUM_RE.finditer(text or "")]


def _normalize_num_str(s: str) -> Optional[float]:
    """
    Normalize numeric string to float.
    Handles PT-BR format (4.281.500.000 or 4,3) and EN-US format.
    """
    if not s:
        return None
    ss = s.strip()
    
    # Heuristic: if has comma and dot, assume dot=thousands, comma=decimal (PT-BR)
    if "," in ss and "." in ss:
        ss = ss.replace(".", "").replace(",", ".")
    else:
        # Only comma -> decimal
        if "," in ss and "." not in ss:
            ss = ss.replace(",", ".")
        # Multiple dots -> thousands separator
        if ss.count(".") > 1:
            ss = ss.replace(".", "")
    
    try:
        return float(ss)
    except Exception:
        return None


def _build_narrative_text(narrative: Dict[str, Any]) -> str:
    """Concatenate all narrative fields for analysis"""
    decision = narrative.get("decision") or {}
    parts = [
        str(narrative.get("executive_summary", "")),
        str(narrative.get("what_changed", "")),
        str(narrative.get("second_order_effect", "")),
        str(narrative.get("risk", "")),
        str(narrative.get("opportunity", "")),
        str(decision.get("if_ignored", "")),
        " ".join(decision.get("what_to_do_next_7d", []) or []),
        " ".join(decision.get("what_to_do_next_30d", []) or []),
        str(narrative.get("confidence_explained", "")),
    ]
    return " ".join(parts)


def validate_narrative(
    insight: Dict[str, Any],
    ready_flags: Dict[str, int],
) -> ValidationResult:
    """
    Validate a narrative against quality gates.
    
    Hard gates:
    - Narrative must exist and be structured
    - No fake zeros when domain offline
    - No numeric claims beyond evidence unless marked as assumption
    - Must include second_order_effect and decision.if_ignored
    
    Returns:
        ValidationResult with pass/fail status, reasons, and flags
    """
    reasons: List[str] = []
    flags: List[str] = []

    domain = insight.get("domain", "").upper()
    evidence = insight.get("evidence", [])
    ev_vals = _flatten_metric_values(evidence)

    narrative = insight.get("narrative") or {}
    status = narrative.get("status", "missing")

    # Gate 1: Basic structure check
    required_fields = [
        "executive_summary",
        "second_order_effect",
        "decision",
    ]
    for field in required_fields:
        if not narrative.get(field):
            reasons.append(f"missing_field:{field}")

    decision = narrative.get("decision") or {}
    if not decision.get("if_ignored"):
        reasons.append("missing_field:decision.if_ignored")
    if not decision.get("what_to_do_next_7d") and not decision.get("what_to_do_next_30d"):
        reasons.append("missing_field:decision.actions")

    # Gate 2: Offline domain check - no zero strings when data unavailable
    ready_key = f"{domain.lower()}_ready"
    domain_ready = int(ready_flags.get(ready_key, 0))
    narrative_text = _build_narrative_text(narrative)

    if domain_ready == 0 and _contains_zero_strings(narrative_text):
        reasons.append("offline_contains_zero_text")
        flags.append("anti_zero_violation")

    # Gate 3: Anti-hyperbole (soft fail -> flag only)
    if _contains_hyperbole(narrative_text):
        flags.append("hyperbole_detected")

    # Gate 4: Numeric grounding check
    assumptions = narrative.get("assumptions") or []
    assume_text = " ".join([str(a) for a in assumptions])
    
    # Build set of evidence numeric values
    ev_num_set = set()
    for v in ev_vals:
        try:
            ev_num_set.add(float(v))
        except (TypeError, ValueError):
            pass

    mentioned_nums = _extract_numbers(narrative_text)
    for num_str in mentioned_nums:
        num = _normalize_num_str(num_str)
        if num is None:
            continue
        
        # Allow if close to evidence (1% tolerance for rounding)
        grounded = False
        if ev_num_set:
            for ev in ev_num_set:
                tolerance = max(0.0001, abs(ev) * 0.01)
                if abs(num - ev) <= tolerance:
                    grounded = True
                    break
        
        if not grounded:
            # Allow if explicitly in assumptions
            if num_str in assume_text:
                grounded = True
        
        if not grounded:
            flags.append("numeric_claim_not_in_evidence")
            # Hard fail only for significant numbers
            if abs(num) >= 1:
                reasons.append(f"number_not_grounded:{num_str}")
                break  # One violation is enough

    # Final determination
    passed = len(reasons) == 0 and status != "missing"
    return ValidationResult(passed=passed, reasons=reasons, flags=flags)


def validate_batch(
    insights: List[Dict[str, Any]],
    ready_flags: Dict[str, int],
) -> Dict[str, ValidationResult]:
    """Validate a batch of insights, return dict keyed by insight id"""
    results = {}
    for insight in insights:
        insight_id = insight.get("id", "unknown")
        results[insight_id] = validate_narrative(insight, ready_flags)
    return results


if __name__ == "__main__":
    # Test case
    test_insight = {
        "id": "TEST_INSIGHT",
        "domain": "JOBS",
        "evidence": [{"metric": "jobs_entry_share", "value": 0.043}],
        "narrative": {
            "status": "ok",
            "executive_summary": "O mercado mostra 4.3% de vagas entry-level.",
            "what_changed": "Queda de 10% em relacao ao mes anterior.",
            "second_order_effect": "Pipeline de talentos comprometido.",
            "risk": "Escassez de profissionais em 3-5 anos.",
            "opportunity": "Empresas que investirem agora terao vantagem.",
            "decision": {
                "what_to_do_next_7d": ["Mapear programas de estagio"],
                "what_to_do_next_30d": ["Lancar programa trainee"],
                "if_ignored": "Custo de contratacao aumentara 25%."
            },
            "assumptions": ["10% e estimativa baseada em historico"],
            "confidence_explained": "Alta confianca nos dados de entrada."
        }
    }
    
    result = validate_narrative(test_insight, {"jobs_ready": 1})
    print(f"Passed: {result.passed}")
    print(f"Reasons: {result.reasons}")
    print(f"Flags: {result.flags}")
