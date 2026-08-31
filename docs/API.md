# UP2CLOUD Assistant API v1

The v1 API exposes explicit feature contracts while preserving `/api/predict` and `/api/cost` for existing clients.

## Design decisions

- Public responses distinguish recommendations, assumptions, risks, confidence, and evidence.
- Conversation history is isolated by `session_id`, bounded to 12 messages, and expires after one hour.
- The public demo does not connect to cloud accounts or accept credentials.
- Terraform generation uses bounded secure templates and static validation. It is not deployment authorization.
- Cost results identify their region, catalog review date, source pages, estimate range, and scenario assumptions.
- Errors use `{ "error": { "code", "message", "request_id", "details" } }`.
- Every API response includes `X-Request-ID`, `X-Response-Time-Ms`, and rate-limit headers.

## Endpoints

### `POST /v1/assist`

```json
{
  "prompt": "Design a phased migration from EC2 to EKS",
  "context": {
    "company_type": "B2B SaaS",
    "current_infrastructure": "EC2 and RDS",
    "challenges": "Zero-downtime migration"
  },
  "session_id": "optional-client-session-id"
}
```

Returns `answer_markdown`, `executive_summary`, `category`, `assumptions`, `recommended_actions`, `risks`, `follow_up_questions`, `references`, `confidence`, and request/session metadata.

### `POST /v1/cost/estimate`

Accepts a validated AWS `us-east-1` workload profile. Optional observed spend and utilization evidence improves the scenario context. Results include baseline, range, breakdown, comparison scenarios, evidence confidence, and pricing provenance.

### `POST /v1/terraform/generate`

Returns a secure Terraform starter as multiple files plus static safety validation. Generated code is deny-by-default and contains no public allow-all CIDR.

### `POST /v1/architecture/generate`

Returns Mermaid source, title, description, component list, and an accessibility summary for `microservices`, `serverless`, or `kubernetes`.

### `POST /v1/security/assess`

Accepts three self-reported controls and optional Terraform, configuration, or policy evidence. Evidence is pattern-checked and reported as `verified`, `adverse`, `reported`, or `not_provided` per control.

### `POST /v1/feedback`

Accepts non-sensitive `helpful` or `not_helpful` feedback for a feature and records it in structured service logs.

## Operational configuration

| Variable | Default | Purpose |
|---|---:|---|
| `RATE_LIMIT_PER_MINUTE` | `60` | Per-client public API limit |
| `LOG_LEVEL` | `INFO` | Structured application log level |

The in-process session and rate-limit stores are intentionally bounded demonstration components. A multi-region or authenticated production service should replace them with a shared store such as Redis.
