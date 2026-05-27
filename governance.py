from datetime import datetime


RULES = [
    {
        "rule_id": "R-001",
        "category": "Safe Knowledge Request",
        "severity": "LOW",
        "decision": "APPROVED",
        "patterns": [
            "explain",
            "describe",
            "analyze",
            "summarize",
            "systems thinking",
            "meaning",
            "history",
            "architecture",
            "philosophy",
            "reasoning",
        ],
    },
    {
        "rule_id": "R-201",
        "category": "Ambiguous Execution Request",
        "severity": "MEDIUM",
        "decision": "CLARIFICATION_REQUIRED",
        "patterns": [
            "handle it",
            "do what needs to be done",
            "take care of it",
            "fix this somehow",
            "however necessary",
        ],
    },
    {
        "rule_id": "R-401",
        "category": "Credential Theft / Unauthorized Access",
        "severity": "HIGH",
        "decision": "REFUSED",
        "patterns": [
            "steal",
            "password",
            "credentials",
            "hack",
            "exploit",
            "bypass",
            "exfiltrate",
            "malware",
            "ransomware",
            "spyware",
            "quietly",
            "without permission",
            "private records",
        ],
    },
]


DECISION_PRIORITY = {
    "REFUSED": 3,
    "CLARIFICATION_REQUIRED": 2,
    "APPROVED": 1,
}


def evaluate_prompt(prompt: str):
    normalized_prompt = prompt.lower()

    matched_rules = []
    matched_patterns = []

    for rule in RULES:
        rule_matches = []

        for pattern in rule["patterns"]:
            if pattern in normalized_prompt:
                rule_matches.append(pattern)
                matched_patterns.append(pattern)

        if rule_matches:
            matched_rules.append(
                {
                    "rule_id": rule["rule_id"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "decision": rule["decision"],
                    "matched_patterns": rule_matches,
                }
            )

    if not matched_rules:
        return build_decision(
            decision="APPROVED",
            severity="LOW",
            risk_category="Unclassified Safe Request",
            matched_rules=[],
            matched_patterns=[],
            reason="No blocking risk detected. Prompt approved for orchestration.",
        )

    highest_rule = sorted(
        matched_rules,
        key=lambda rule: DECISION_PRIORITY[rule["decision"]],
        reverse=True,
    )[0]

    if highest_rule["decision"] == "REFUSED":
        return build_decision(
            decision="REFUSED",
            severity="HIGH",
            risk_category=highest_rule["category"],
            matched_rules=matched_rules,
            matched_patterns=matched_patterns,
            reason="Unsafe intent detected. Orchestration blocked.",
        )

    if highest_rule["decision"] == "CLARIFICATION_REQUIRED":
        return build_decision(
            decision="CLARIFICATION_REQUIRED",
            severity="MEDIUM",
            risk_category=highest_rule["category"],
            matched_rules=matched_rules,
            matched_patterns=matched_patterns,
            reason="Ambiguous intent detected. Clarification required before orchestration.",
        )

    return build_decision(
        decision="APPROVED",
        severity="LOW",
        risk_category=highest_rule["category"],
        matched_rules=matched_rules,
        matched_patterns=matched_patterns,
        reason="Prompt approved for orchestration.",
    )


def build_decision(
    decision,
    severity,
    risk_category,
    matched_rules,
    matched_patterns,
    reason,
):
    execution_gate = "OPEN"

    if decision in ["REFUSED", "CLARIFICATION_REQUIRED"]:
        execution_gate = "CLOSED"

    confidence = calculate_confidence(
        decision=decision,
        matched_patterns=matched_patterns,
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "decision": decision,
        "severity": severity,
        "confidence": confidence,
        "risk_category": risk_category,
        "execution_gate": execution_gate,
        "reason": reason,
        "matched_patterns": matched_patterns,
        "matched_rules": matched_rules,
        "trigger_path": build_trigger_path(matched_rules),
        "governance_rationale": build_rationale(
            decision=decision,
            severity=severity,
            risk_category=risk_category,
            matched_patterns=matched_patterns,
        ),
    }


def calculate_confidence(decision, matched_patterns):
    match_count = len(matched_patterns)

    if decision == "REFUSED":
        return min(0.99, 0.75 + (match_count * 0.06))

    if decision == "CLARIFICATION_REQUIRED":
        return min(0.90, 0.60 + (match_count * 0.08))

    if match_count > 0:
        return min(0.85, 0.55 + (match_count * 0.05))

    return 0.50


def build_trigger_path(matched_rules):
    trigger_path = []

    for rule in matched_rules:
        trigger_path.append(
            {
                "rule_id": rule["rule_id"],
                "category": rule["category"],
                "decision": rule["decision"],
                "matched_patterns": rule["matched_patterns"],
            }
        )

    return trigger_path


def build_rationale(decision, severity, risk_category, matched_patterns):
    if decision == "REFUSED":
        return (
            f"The request was refused because it matched high-risk governance triggers "
            f"associated with {risk_category}. Matched patterns: {matched_patterns}. "
            f"Execution gate remains closed."
        )

    if decision == "CLARIFICATION_REQUIRED":
        return (
            f"The request requires clarification because it matched ambiguous execution triggers "
            f"associated with {risk_category}. Matched patterns: {matched_patterns}. "
            f"Execution gate remains closed until the operator clarifies intent."
        )

    return (
        f"The request was approved with severity {severity}. "
        f"Risk category: {risk_category}. "
        f"No blocking governance rule closed the execution gate."
    )