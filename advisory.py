"""Deterministic, structured cloud advisory engine used by the public demo."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


PLAYBOOKS: dict[str, dict[str, Any]] = {
    "kubernetes_migration": {
        "category": "Kubernetes migration",
        "executive_summary": (
            "Use an incremental migration with an explicit readiness baseline, a reversible first workload, "
            "and production evidence before scaling adoption. Kubernetes should solve an operating problem, "
            "not merely replace virtual machines."
        ),
        "actions": [
            ("Establish the platform baseline", "Define identity, networking, secrets, policy, observability, and ownership before migrating workloads.", "Now"),
            ("Select a low-risk pilot", "Choose a stateless service with measurable traffic, limited dependencies, and a tested rollback path.", "Next"),
            ("Run parallel delivery", "Use weighted traffic, SLOs, synthetic tests, and database compatibility checks before cutover.", "Next"),
            ("Scale through paved roads", "Publish reusable deployment, policy, and telemetry templates after the pilot proves the operating model.", "Later"),
        ],
        "risks": [
            ("Platform complexity", "A cluster without clear ownership and golden paths can increase delivery lead time.", "high"),
            ("State migration", "Database and session coupling can make rollback harder than compute migration.", "high"),
            ("Observability gaps", "Missing application-level SLOs can hide regressions during traffic shifting.", "medium"),
        ],
        "references": [
            ("Kubernetes production environment guidance", "https://kubernetes.io/docs/setup/production-environment/"),
            ("AWS EKS best practices", "https://docs.aws.amazon.com/eks/latest/best-practices/introduction.html"),
        ],
    },
    "finops": {
        "category": "FinOps and cost optimization",
        "executive_summary": (
            "Start with allocation and waste removal, then optimize rates only after the workload baseline is stable. "
            "Every saving should have an owner, a confidence range, and a reliability guardrail."
        ),
        "actions": [
            ("Create a trusted cost baseline", "Reconcile billing data, ownership tags, shared-cost allocation, and unit economics for the last 90 days.", "Now"),
            ("Remove idle and oversized capacity", "Prioritize unattached storage, stopped resources, low-utilization compute, and non-production schedules.", "Now"),
            ("Tune architecture", "Review storage tiers, data transfer, autoscaling, database sizing, and serverless execution patterns.", "Next"),
            ("Commit only proven demand", "Model Savings Plans or reservations after usage is stable and rollback risk is understood.", "Later"),
        ],
        "risks": [
            ("False savings", "Reducing redundancy or observability can move cost into incidents and recovery time.", "high"),
            ("Coverage mismatch", "Long commitments made before rightsizing can lock in avoidable spend.", "medium"),
            ("Weak allocation", "Unowned spend prevents durable accountability and forecasting.", "medium"),
        ],
        "references": [
            ("FinOps Framework", "https://www.finops.org/framework/"),
            ("AWS Cost Optimization Pillar", "https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html"),
        ],
    },
    "security": {
        "category": "Cloud security and governance",
        "executive_summary": (
            "Build security as a platform capability: centralized identity, preventative guardrails, immutable audit evidence, "
            "and automated remediation. Treat compliance as an output of continuously verified controls."
        ),
        "actions": [
            ("Centralize identity", "Use federated SSO, phishing-resistant MFA, short-lived roles, and emergency access with monitoring.", "Now"),
            ("Separate blast radii", "Organize workloads by account or subscription, environment, data sensitivity, and clear network boundaries.", "Now"),
            ("Create the evidence plane", "Centralize audit logs, configuration history, findings, and retention in a protected security account.", "Next"),
            ("Automate guardrails", "Enforce encryption, approved regions, public-access controls, and policy checks in CI/CD and at runtime.", "Next"),
        ],
        "risks": [
            ("Privilege sprawl", "Long-lived credentials and broad roles increase account-takeover impact.", "critical"),
            ("Unmonitored exceptions", "Manual policy exceptions can silently become permanent exposure.", "high"),
            ("Evidence gaps", "Controls that cannot be demonstrated continuously create audit and incident risk.", "medium"),
        ],
        "references": [
            ("AWS Security Pillar", "https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html"),
            ("CIS Controls", "https://www.cisecurity.org/controls"),
        ],
    },
    "reliability": {
        "category": "Reliability engineering",
        "executive_summary": (
            "Diagnose production errors through a time-bounded evidence trail: user impact, request path, dependency health, "
            "and recent changes. Restore service first, then remove the failure mode with measurable controls."
        ),
        "actions": [
            ("Define impact and timeline", "Quantify affected requests, regions, tenants, status codes, and the first observed timestamp.", "Now"),
            ("Trace the request path", "Correlate load balancer, ingress, application, dependency, and platform signals using one request ID.", "Now"),
            ("Compare recent change", "Review deployments, configuration, scaling, certificates, DNS, and dependency changes around the start time.", "Next"),
            ("Harden the failure mode", "Add an SLO, alert, runbook, synthetic test, and rollback trigger for the confirmed cause.", "Later"),
        ],
        "risks": [
            ("Metric-only diagnosis", "Aggregate metrics can hide tenant-specific or dependency-specific failures.", "high"),
            ("Retry amplification", "Unbounded retries can turn a partial dependency failure into systemic overload.", "high"),
            ("Premature root cause", "A recent deployment may correlate with the incident without causing it.", "medium"),
        ],
        "references": [
            ("Google SRE incident response", "https://sre.google/sre-book/managing-incidents/"),
            ("AWS Reliability Pillar", "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html"),
        ],
    },
    "architecture": {
        "category": "Cloud architecture",
        "executive_summary": (
            "Choose architecture from business constraints and failure modes, then validate it with measurable quality attributes. "
            "Prefer the simplest platform that satisfies availability, security, delivery, and cost requirements."
        ),
        "actions": [
            ("Capture quality attributes", "Make availability, latency, RTO/RPO, compliance, growth, and budget explicit and testable.", "Now"),
            ("Map critical flows", "Document trust boundaries, synchronous dependencies, state ownership, and failure propagation.", "Now"),
            ("Compare two viable options", "Score alternatives on delivery speed, operational load, cost, resilience, and reversibility.", "Next"),
            ("Prove the riskiest assumption", "Use a focused spike or load test before committing to the full platform design.", "Next"),
        ],
        "risks": [
            ("Premature complexity", "Multiple platforms or services can outpace the team's operating capacity.", "high"),
            ("Unclear ownership", "Shared components without service ownership create slow incident response.", "medium"),
            ("Untested recovery", "A diagram is not resilient until backup, failover, and restoration are exercised.", "high"),
        ],
        "references": [
            ("AWS Well-Architected Framework", "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"),
            ("Google Cloud Architecture Framework", "https://cloud.google.com/architecture/framework"),
        ],
    },
}


def classify_prompt(prompt: str) -> str:
    """Route a question to the closest professional cloud playbook."""

    normalized = prompt.lower()
    if any(term in normalized for term in ("migrate", "migration", "eks", "kubernetes", "k8s", "container")):
        return "kubernetes_migration"
    if any(term in normalized for term in ("cost", "finops", "saving", "rightsiz", "bill", "spend")):
        return "finops"
    if any(term in normalized for term in ("security", "secure", "audit", "mfa", "identity", "compliance", "landing zone")):
        return "security"
    if any(term in normalized for term in ("5xx", "incident", "outage", "latency", "reliability", "troubleshoot", "error")):
        return "reliability"
    return "architecture"


def build_advisory_response(
    prompt: str,
    context: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create an explainable response contract without pretending to inspect an account."""

    context = context or {}
    history = history or []
    playbook_key = classify_prompt(prompt)
    playbook = PLAYBOOKS[playbook_key]

    known_context = [
        value
        for value in (
            context.get("company_type"),
            context.get("current_infrastructure"),
            context.get("challenges"),
        )
        if value
    ]
    assumptions = []
    if context.get("company_type"):
        assumptions.append(f"The organisation operates as {context['company_type']}.")
    if context.get("current_infrastructure"):
        assumptions.append(f"Current platform context: {context['current_infrastructure']}.")
    if context.get("challenges"):
        assumptions.append(f"Primary stated challenge: {context['challenges']}.")
    if not assumptions:
        assumptions.extend([
            "No account or production telemetry was inspected.",
            "Recommendations assume a production workload where security and reversibility matter.",
        ])

    follow_up_questions = []
    if not context.get("current_infrastructure"):
        follow_up_questions.append("Which cloud services, environments, and dependencies are currently in scope?")
    if not context.get("challenges"):
        follow_up_questions.append("What measurable outcome and deadline define success?")
    if playbook_key in {"architecture", "kubernetes_migration"}:
        follow_up_questions.append("What are the availability target and recovery objectives (RTO/RPO)?")
    if playbook_key == "finops":
        follow_up_questions.append("What is the last 90 days of spend by service, account, and environment?")

    actions = [
        {"title": title, "rationale": rationale, "priority": priority}
        for title, rationale, priority in playbook["actions"]
    ]
    risks = [
        {"title": title, "detail": detail, "severity": severity}
        for title, detail, severity in playbook["risks"]
    ]
    references = [
        {"title": title, "url": url}
        for title, url in playbook["references"]
    ]

    action_markdown = "\n".join(
        f"{index}. **{action['title']}** — {action['rationale']}"
        for index, action in enumerate(actions, 1)
    )
    risk_markdown = "\n".join(
        f"- **{risk['title']} ({risk['severity']})** — {risk['detail']}"
        for risk in risks
    )
    answer_markdown = (
        f"## Recommendation\n\n{playbook['executive_summary']}\n\n"
        f"## Delivery sequence\n\n{action_markdown}\n\n"
        f"## Risks to control\n\n{risk_markdown}"
    )

    confidence = 0.9 if len(known_context) >= 3 else 0.82 if known_context else 0.68
    return {
        "answer_markdown": answer_markdown,
        "executive_summary": playbook["executive_summary"],
        "category": playbook["category"],
        "assumptions": assumptions,
        "recommended_actions": actions,
        "risks": risks,
        "follow_up_questions": follow_up_questions,
        "references": references,
        "confidence": confidence,
        "advisory_mode": "evidence-informed guidance",
        "provider": "up2cloud-structured-advisor-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "history_turns_considered": min(len(history), 6),
    }
