"""
UP2CLOUD AI Cloud Engineering Assistant Model - Premium Edition
Specialized conversational model for cloud architecture, DevOps, FinOps, and platform engineering guidance.
Now with enhanced features: cost estimation, code generation, architecture diagrams, security scanning,
Slack/Teams integration, document processing, and multi-turn conversation memory.
"""

import re
import threading
import time
import uuid
from typing import Optional, Dict, Any

from advisory import build_advisory_response
from enhanced_features import (
    CostEstimator, CodeGenerator, ArchitectureDiagrammer, 
    SecurityScanner
)
from integrations import SlackIntegration, TeamsIntegration, DocumentUploadHandler


class SessionStore:
    """Bounded, isolated in-process conversation history for the public demo."""

    def __init__(self, ttl_seconds: int = 3600, max_sessions: int = 500, max_messages: int = 12):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self.max_messages = max_messages
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def resolve(self, requested_session_id: str | None = None) -> str:
        if requested_session_id and re.fullmatch(r"[A-Za-z0-9_-]{8,80}", requested_session_id):
            return requested_session_id
        return uuid.uuid4().hex

    def history(self, session_id: str) -> list[dict[str, Any]]:
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            session = self._sessions.setdefault(session_id, {"updated_at": now, "messages": []})
            session["updated_at"] = now
            return list(session["messages"])

    def add(self, session_id: str, role: str, content: str, context: dict | None = None) -> None:
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            session = self._sessions.setdefault(session_id, {"updated_at": now, "messages": []})
            session["updated_at"] = now
            session["messages"].append({"role": role, "content": content, "context": context})
            session["messages"] = session["messages"][-self.max_messages:]

            if len(self._sessions) > self.max_sessions:
                oldest = min(self._sessions, key=lambda key: self._sessions[key]["updated_at"])
                self._sessions.pop(oldest, None)

    def _prune(self, now: float) -> None:
        expired = [
            key
            for key, value in self._sessions.items()
            if now - value["updated_at"] > self.ttl_seconds
        ]
        for key in expired:
            self._sessions.pop(key, None)


SESSION_STORE = SessionStore()


def init():
    """Initialize the model with UP2CLOUD's system prompt and configuration."""
    return {
        "model_name": "up2cloud-engineering-assistant-premium",
        "version": "2.0.0",
        "provider": "anthropic",
        "features": [
            "conversational-qa",
            "cost-estimation",
            "code-generation",
            "architecture-diagrams",
            "security-scanning",
            "slack-integration",
            "teams-integration",
            "document-processing",
            "multi-turn-memory",
            "webhook-support"
        ]
    }


def predict(
    prompt: str,
    context: Optional[dict] = None,
    features: Optional[dict] = None,
    session_id: Optional[str] = None,
) -> dict:
    """
    Main inference endpoint for the UP2CLOUD AI assistant.
    Now supports enhanced features: cost estimation, code generation, diagrams, security scanning, etc.
    
    Args:
        prompt: User's technical question or request
        context: Optional context about the user's infrastructure/situation
        features: Optional dict to enable specific features:
            - estimate_cost: Generate cost estimation
            - generate_code: Generate Terraform/CloudFormation
            - architecture_diagram: Generate architecture diagram
            - security_scan: Perform security audit
            - slack_format: Format response for Slack
            - teams_format: Format response for Teams
            - upload_file: Analyze uploaded document
    
    Returns:
        dict with assistant response and metadata
    """
    
    resolved_session_id = SESSION_STORE.resolve(session_id)
    history = SESSION_STORE.history(resolved_session_id)
    advisory = build_advisory_response(prompt, context, history)
    response = advisory["answer_markdown"]
    SESSION_STORE.add(resolved_session_id, "user", prompt, context)

    security_findings = None
    if features and features.get("security_scan") and context:
        security_findings = SecurityScanner.scan_infrastructure(context)
        response = security_findings["summary"]
    
    SESSION_STORE.add(resolved_session_id, "assistant", response)
    
    result = {
        "response": response,
        "model": "up2cloud-structured-advisor-v1",
        "advisory": advisory,
        "usage": {
            "input_tokens": len(prompt.split()),
            "output_tokens": len(response.split()) if response else 0,
        },
        "session_id": resolved_session_id,
        "turn_number": len(SESSION_STORE.history(resolved_session_id)),
    }
    
    # Process optional features
    if features:
        if features.get("estimate_cost") and context:
            cost_estimate = CostEstimator.estimate_monthly_cost(context)
            result["cost_estimate"] = cost_estimate
        
        if features.get("generate_code"):
            terraform_bundle = CodeGenerator.generate_terraform_bundle(prompt, context or {})
            result["terraform"] = terraform_bundle
            result["terraform_code"] = terraform_bundle["combined_code"]
        
        if features.get("architecture_diagram"):
            diagram_type = features.get("diagram_type", "microservices")
            architecture = ArchitectureDiagrammer.generate_architecture(diagram_type)
            result["architecture"] = architecture
            result["architecture_diagram"] = architecture["diagram"]
        
        if security_findings is not None:
            result["security_audit"] = security_findings
        
        if features.get("slack_format"):
            result["formatted_response"] = SlackIntegration.format_response(response, {
                "model": result["model"],
                "category": "Cloud Engineering"
            })
        
        if features.get("teams_format"):
            result["formatted_response"] = TeamsIntegration.format_response(response)
        
        if features.get("upload_file"):
            file_analysis = DocumentUploadHandler.process_upload(
                features.get("file_name", "document"),
                features.get("file_content", "")
            )
            result["document_analysis"] = file_analysis
    
    return result


def generate_response(system_prompt: str, messages: list) -> str:
    """
    Generate a structured, deterministic advisory response.
    """
    user_question = messages[-1]["content"]
    return build_advisory_response(user_question, history=messages[:-1])["answer_markdown"]


if __name__ == "__main__":
    # Test the model locally
    init()
    
    # Example queries
    test_queries = [
        "How can we optimize our AWS costs for a startup with variable workloads?",
        "What's the best approach to migrate from monolithic to microservices on Kubernetes?",
        "How do we implement proper FinOps practices in our organization?",
        "Can you help us design a multi-cloud strategy?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = predict(query)
        print(f"Response: {result['response']}")
        print(f"Tokens: {result['usage']}")
