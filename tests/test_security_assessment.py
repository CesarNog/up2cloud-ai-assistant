import unittest

from enhanced_features import SecurityScanner
from model import predict


class SecurityScannerTests(unittest.TestCase):
    def test_all_controls_enabled_returns_complete_low_risk_baseline(self):
        audit = SecurityScanner.scan_infrastructure({
            "encryption_enabled": True,
            "mfa_enabled": True,
            "restrict_security_groups": True,
        })

        self.assertEqual(audit["score"], 100)
        self.assertEqual(audit["risk_level"], "Low")
        self.assertEqual(audit["evaluated_checks"], 3)
        self.assertEqual(audit["passed_checks"], 3)
        self.assertEqual(audit["priority_actions"], 0)
        self.assertEqual({check["status"] for check in audit["checks"]}, {"pass"})

    def test_missing_controls_returns_prioritized_critical_findings(self):
        audit = SecurityScanner.scan_infrastructure({
            "encryption_enabled": False,
            "mfa_enabled": False,
            "restrict_security_groups": False,
        })

        self.assertEqual(audit["score"], 0)
        self.assertEqual(audit["risk_level"], "Critical")
        self.assertEqual(audit["priority_actions"], 3)
        self.assertEqual(
            {check["id"] for check in audit["checks"]},
            {"encryption_at_rest", "mfa", "security_groups"},
        )
        self.assertTrue(all(check["recommendation"] for check in audit["checks"]))

    def test_weighted_score_uses_only_evaluated_controls(self):
        audit = SecurityScanner.scan_infrastructure({
            "encryption_enabled": True,
            "mfa_enabled": True,
            "restrict_security_groups": False,
        })

        self.assertEqual(audit["score"], 75)
        self.assertEqual(audit["risk_level"], "Moderate")
        self.assertEqual(audit["passed_checks"], 2)
        self.assertEqual(audit["priority_actions"], 1)
        self.assertIn("gap requires action", audit["summary"])

    def test_predict_exposes_assessment_summary_instead_of_placeholder(self):
        result = predict(
            "Perform security audit",
            context={
                "encryption_enabled": True,
                "mfa_enabled": False,
                "restrict_security_groups": True,
            },
            features={"security_scan": True},
        )

        self.assertIn("security_audit", result)
        self.assertEqual(result["response"], result["security_audit"]["summary"])
        self.assertNotIn("Response generated for", result["response"])


if __name__ == "__main__":
    unittest.main()
