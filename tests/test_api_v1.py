import unittest

from fastapi.testclient import TestClient

from app import app


class ApiV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_assist_returns_structured_contract_and_isolated_session(self):
        response = self.client.post("/v1/assist", json={
            "prompt": "Design a phased zero-downtime migration from EC2 to Amazon EKS",
            "context": {
                "company_type": "B2B SaaS",
                "current_infrastructure": "EC2 and RDS",
                "challenges": "Zero-downtime delivery",
            },
            "session_id": "test-session-one",
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["category"], "Kubernetes migration")
        self.assertGreaterEqual(len(body["recommended_actions"]), 4)
        self.assertGreaterEqual(len(body["risks"]), 3)
        self.assertNotIn("Response generated for", body["answer_markdown"])
        self.assertEqual(body["session_id"], "test-session-one")
        self.assertEqual(body["turn_number"], 2)
        self.assertEqual(response.headers["x-request-id"], body["request_id"])
        self.assertIn("x-response-time-ms", response.headers)
        self.assertIn("x-ratelimit-remaining", response.headers)

        isolated = self.client.post("/v1/assist", json={
            "prompt": "Create a practical AWS cost optimization plan",
            "session_id": "test-session-two",
        }).json()
        self.assertEqual(isolated["turn_number"], 2)
        self.assertEqual(isolated["history_turns_considered"], 0)

    def test_terraform_is_secure_by_default_and_validated(self):
        response = self.client.post("/v1/terraform/generate", json={
            "requirement": "Generate Terraform for a production AWS network foundation",
            "aws_region": "us-east-1",
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["validation"]["status"], "passed")
        self.assertNotIn("0.0.0.0/0", body["combined_code"])
        self.assertIn("map_public_ip_on_launch = false", body["combined_code"])
        self.assertIn("enable_key_rotation", body["combined_code"])
        self.assertEqual({file["name"] for file in body["files"]}, {"versions.tf", "variables.tf", "main.tf", "outputs.tf"})

    def test_cost_contract_rejects_negative_values(self):
        response = self.client.post("/v1/cost/estimate", json={
            "infrastructure": {"s3_storage_gb": -1}
        })

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "validation_error")
        self.assertTrue(error["request_id"])

    def test_cost_result_includes_scenarios_evidence_and_pricing_metadata(self):
        response = self.client.post("/v1/cost/estimate", json={
            "infrastructure": {
                "provider": "aws",
                "region": "us-east-1",
                "ec2_instances": [{"type": "t3.medium", "count": 2}],
                "s3_storage_gb": 100,
                "evidence": {
                    "observed_monthly_spend": 150,
                    "average_compute_utilization_percent": 35,
                    "evidence_source": "billing export",
                },
            }
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["scenarios"]), 3)
        self.assertEqual(body["evidence"]["confidence"], "high")
        self.assertEqual(body["pricing_metadata"]["region"], "us-east-1")
        self.assertTrue(body["pricing_metadata"]["last_reviewed"])
        self.assertLess(body["estimate_range"]["low"], body["estimate_range"]["high"])

    def test_security_evidence_can_verify_and_contradict_controls(self):
        response = self.client.post("/v1/security/assess", json={
            "context": {
                "encryption_enabled": False,
                "mfa_enabled": True,
                "restrict_security_groups": True,
                "evidence_source": "terraform",
                "evidence_text": "kms_key_id = aws_kms_key.data.arn\nsecurity_group = true\ncidr_blocks = [\"0.0.0.0/0\"]",
            }
        })

        self.assertEqual(response.status_code, 200)
        body = response.json()
        checks = {check["id"]: check for check in body["checks"]}
        self.assertEqual(checks["encryption_at_rest"]["evidence"]["status"], "verified")
        self.assertEqual(checks["security_groups"]["status"], "warning")
        self.assertEqual(checks["security_groups"]["evidence"]["status"], "adverse")
        self.assertEqual(body["evidence_summary"]["mode"], "evidence_assisted")

    def test_architecture_has_accessible_metadata_and_no_emoji(self):
        response = self.client.post("/v1/architecture/generate", json={"pattern": "microservices"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["format"], "mermaid")
        self.assertGreater(len(body["components"]), 4)
        self.assertTrue(body["accessibility_summary"])
        self.assertFalse(any(ord(character) > 0xFFFF for character in body["diagram"]))

    def test_feedback_uses_typed_contract(self):
        response = self.client.post("/v1/feedback", json={
            "feature": "qa",
            "rating": "helpful",
            "request_id": "request-123",
        })

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["status"], "recorded")


if __name__ == "__main__":
    unittest.main()
