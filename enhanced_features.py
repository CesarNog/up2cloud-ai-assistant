"""
UP2CLOUD Model - Enhanced Features Module
Adds cost estimation, code generation, architecture diagramming, and more.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


class CostEstimator:
    """Real-time cost estimation for AWS/GCP/Azure."""
    
    AWS_PRICING = {
        "ec2": {
            "t3.medium": 0.0416,  # per hour, on-demand
            "t3.large": 0.0832,
            "m5.large": 0.096,
            "m5.xlarge": 0.192,
            "c5.large": 0.085,
            "c5.xlarge": 0.17,
        },
        "rds": {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.m5.large": 0.20,
            "db.m5.xlarge": 0.40,
        },
        "s3": {
            "storage_gb": 0.023,
            "requests_1k": 0.0004,  # per 1000 requests
        },
        "lambda": {
            "per_gb_second": 0.0000166667,
            "per_million_requests": 0.20,
        }
    }
    
    @staticmethod
    def estimate_monthly_cost(infrastructure: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate monthly costs for given infrastructure."""
        total_cost = 0
        breakdown = {}
        
        # EC2 estimation
        if "ec2_instances" in infrastructure:
            ec2_cost = 0
            for instance in infrastructure["ec2_instances"]:
                instance_type = instance.get("type", "t3.medium")
                count = instance.get("count", 1)
                hourly_rate = CostEstimator.AWS_PRICING["ec2"].get(instance_type, 0.05)
                monthly_cost = hourly_rate * 730 * count  # 730 hours per month
                ec2_cost += monthly_cost
            breakdown["EC2"] = ec2_cost
            total_cost += ec2_cost
        
        # RDS estimation
        if "rds_instances" in infrastructure:
            rds_cost = 0
            for db in infrastructure["rds_instances"]:
                db_type = db.get("type", "db.t3.micro")
                hourly_rate = CostEstimator.AWS_PRICING["rds"].get(db_type, 0.017)
                monthly_cost = hourly_rate * 730
                rds_cost += monthly_cost
            breakdown["RDS"] = rds_cost
            total_cost += rds_cost
        
        # S3 estimation
        if "s3_storage_gb" in infrastructure:
            s3_cost = infrastructure["s3_storage_gb"] * CostEstimator.AWS_PRICING["s3"]["storage_gb"]
            breakdown["S3"] = s3_cost
            total_cost += s3_cost
        
        # Lambda estimation
        if "lambda_requests" in infrastructure:
            lambda_cost = (infrastructure["lambda_requests"] / 1_000_000) * CostEstimator.AWS_PRICING["lambda"]["per_million_requests"]
            breakdown["Lambda"] = lambda_cost
            total_cost += lambda_cost
        
        return {
            "estimated_monthly_cost": round(total_cost, 2),
            "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
            "currency": "USD",
            "period": "monthly"
        }


class CodeGenerator:
    """Generate Infrastructure as Code templates."""
    
    @staticmethod
    def generate_terraform(architecture: Dict[str, Any]) -> str:
        """Generate Terraform configuration from architecture description."""
        tf_config = """# Generated Terraform Configuration for UP2CLOUD Architecture
# Auto-generated - review and customize as needed

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "vpc-${var.environment}"
  }
}

# Subnets
resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "subnet-public-${var.environment}"
  }
}

# Security Group
resource "aws_security_group" "app" {
  name        = "sg-app-${var.environment}"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "vpc_cidr" {
  value = aws_vpc.main.cidr_block
}
"""
        return tf_config

    @staticmethod
    def generate_cloudformation(architecture: Dict[str, Any]) -> str:
        """Generate CloudFormation template."""
        cf_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "UP2CLOUD Auto-Generated CloudFormation Template",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": "production",
                    "AllowedValues": ["development", "staging", "production"]
                }
            },
            "Resources": {
                "VPC": {
                    "Type": "AWS::EC2::VPC",
                    "Properties": {
                        "CidrBlock": "10.0.0.0/16",
                        "EnableDnsHostnames": True,
                        "EnableDnsSupport": True,
                        "Tags": [{"Key": "Name", "Value": {"Fn::Sub": "vpc-${Environment}"}}]
                    }
                },
                "PublicSubnet": {
                    "Type": "AWS::EC2::Subnet",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "CidrBlock": "10.0.1.0/24",
                        "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": ""}]},
                    }
                },
                "SecurityGroup": {
                    "Type": "AWS::EC2::SecurityGroup",
                    "Properties": {
                        "GroupDescription": "Application Security Group",
                        "VpcId": {"Ref": "VPC"},
                        "SecurityGroupIngress": [
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 443,
                                "ToPort": 443,
                                "CidrIp": "0.0.0.0/0"
                            }
                        ]
                    }
                }
            },
            "Outputs": {
                "VpcId": {"Value": {"Ref": "VPC"}},
                "VpcCidr": {"Value": {"Fn::GetAtt": ["VPC", "CidrBlock"]}}
            }
        }
        return json.dumps(cf_template, indent=2)


class ArchitectureDiagrammer:
    """Generate Mermaid diagrams for architecture visualization."""
    
    @staticmethod
    def generate_diagram(architecture_type: str) -> str:
        """Generate Mermaid diagram for infrastructure architecture."""
        
        diagrams = {
            "microservices": """
graph TB
    User["👤 Users"]
    CDN["🌐 CloudFront<br/>CDN"]
    ALB["⚙️ Application<br/>Load Balancer"]
    
    subgraph "Microservices"
        Auth["🔐 Auth Service<br/>ECS"]
        API["📡 API Service<br/>ECS"]
        Worker["⚙️ Worker Service<br/>ECS"]
    end
    
    subgraph "Data Layer"
        DB["🗄️ RDS Aurora<br/>PostgreSQL"]
        Cache["⚡ ElastiCache<br/>Redis"]
        Queue["📦 SQS<br/>Message Queue"]
    end
    
    subgraph "Monitoring & Logging"
        Logs["📊 CloudWatch<br/>Logs"]
        Metrics["📈 CloudWatch<br/>Metrics"]
    end
    
    User -->|HTTPS| CDN
    CDN -->|Cache Miss| ALB
    ALB -->|Routes| Auth
    ALB -->|Routes| API
    API --> Worker
    Auth -->|Read/Write| DB
    API -->|Read/Write| DB
    Worker -->|Consume| Queue
    Worker -->|Cache| Cache
    Auth -.->|Logs| Logs
    API -.->|Metrics| Metrics
    
    style User fill:#e1f5ff
    style CDN fill:#fff3e0
    style ALB fill:#fff3e0
    style Auth fill:#c8e6c9
    style API fill:#c8e6c9
    style Worker fill:#c8e6c9
    style DB fill:#f8bbd0
    style Cache fill:#f8bbd0
    style Queue fill:#f8bbd0
            """,
            
            "serverless": """
graph TB
    Client["👤 Client"]
    APIGW["🔗 API Gateway"]
    Lambda["⚡ Lambda Functions"]
    
    subgraph "Compute"
        L1["📝 Endpoint 1"]
        L2["📝 Endpoint 2"]
        L3["🔄 Background Job"]
    end
    
    subgraph "Storage"
        S3["🪣 S3 Bucket"]
        DDB["🗄️ DynamoDB"]
    end
    
    subgraph "Events & Messaging"
        SNS["📢 SNS Topics"]
        SQS["📦 SQS Queues"]
        Events["📅 EventBridge"]
    end
    
    Client -->|HTTP/REST| APIGW
    APIGW --> L1
    APIGW --> L2
    Events --> L3
    L1 -->|Read/Write| DDB
    L2 -->|Upload| S3
    L3 -->|Process| S3
    L1 -.->|Publish| SNS
    SNS -.->|Trigger| L3
    Events -.->|Schedule| L3
    
    style Client fill:#e1f5ff
    style APIGW fill:#fff3e0
    style Lambda fill:#c8e6c9
    style L1 fill:#c8e6c9
    style L2 fill:#c8e6c9
    style L3 fill:#c8e6c9
    style S3 fill:#f8bbd0
    style DDB fill:#f8bbd0
            """,
            
            "kubernetes": """
graph TB
    Users["👥 Users"]
    LB["🔗 Load Balancer<br/>Service"]
    
    subgraph "Kubernetes Cluster"
        subgraph "Ingress"
            Ingress["📥 Ingress Controller"]
        end
        
        subgraph "Workloads"
            DP1["🐳 API Pod<br/>Deployment"]
            DP2["🐳 Web Pod<br/>Deployment"]
            SS["🐳 Stateful Pod<br/>StatefulSet"]
        end
        
        subgraph "Services"
            SVC1["Service: api"]
            SVC2["Service: web"]
            SVC3["Service: db"]
        end
        
        subgraph "Storage"
            PV["💾 Persistent<br/>Volume"]
            CM["📋 ConfigMap"]
        end
    end
    
    Registry["📦 Container Registry<br/>ECR/Docker Hub"]
    
    Users -->|HTTPS| LB
    LB --> Ingress
    Ingress --> SVC1
    Ingress --> SVC2
    SVC1 --> DP1
    SVC2 --> DP2
    SVC3 --> SS
    SS --> PV
    DP1 -.->|Pull| Registry
    DP2 -.->|Pull| Registry
    SS -.->|Config| CM
    
    style Users fill:#e1f5ff
    style LB fill:#fff3e0
    style Ingress fill:#fff3e0
    style DP1 fill:#c8e6c9
    style DP2 fill:#c8e6c9
    style SS fill:#c8e6c9
    style SVC1 fill:#fff9c4
    style SVC2 fill:#fff9c4
    style SVC3 fill:#fff9c4
            """
        }
        
        return diagrams.get(architecture_type, diagrams["microservices"])


class ConversationMemory:
    """Multi-turn conversation memory management."""
    
    def __init__(self):
        self.conversation_history = []
        self.session_id = datetime.now().isoformat()
        self.created_at = datetime.now()
    
    def add_message(self, role: str, content: str, context: Optional[Dict] = None):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "context": context
        })
    
    def get_context_summary(self) -> str:
        """Generate summary of conversation context."""
        if not self.conversation_history:
            return "No conversation history"
        
        summary = f"Session ID: {self.session_id}\n"
        summary += f"Messages: {len(self.conversation_history)}\n"
        summary += f"Topics discussed:\n"
        
        for i, msg in enumerate(self.conversation_history, 1):
            summary += f"  {i}. {msg['content'][:60]}...\n"
        
        return summary
    
    def get_recent_context(self, num_messages: int = 5) -> List[Dict]:
        """Get recent conversation context."""
        return self.conversation_history[-num_messages:]


class SecurityScanner:
    """Validate infrastructure against security best practices."""
    
    RULES = {
        "encryption_at_rest": "All data stores must have encryption at rest enabled",
        "encryption_in_transit": "All communications must use TLS 1.2+",
        "security_groups": "Security groups must have explicit allow rules (no allow-all)",
        "iam_least_privilege": "IAM policies must follow least privilege principle",
        "mfa": "Administrative accounts must have MFA enabled",
        "audit_logging": "All resources must have audit logging enabled",
        "backup_strategy": "Critical data must have backup strategy defined",
        "network_isolation": "Resources must be in isolated VPCs/subnets"
    }

    CONTROL_WEIGHTS = {
        "encryption_at_rest": 35,
        "mfa": 40,
        "security_groups": 25,
    }
    
    @staticmethod
    def scan_infrastructure(infrastructure: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the three controls provided by the lightweight web profile."""
        findings = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "checks": [],
        }

        if infrastructure.get("encryption_enabled"):
            findings["passed"].append("✅ Encryption at rest enabled")
            findings["checks"].append({
                "id": "encryption_at_rest",
                "title": "Encryption at rest",
                "status": "pass",
                "severity": "informational",
                "finding": "Data stores and snapshots are reported as encrypted at rest.",
                "recommendation": "Verify coverage, customer-managed key ownership, rotation, and backup encryption.",
            })
        else:
            findings["failed"].append("❌ Encryption at rest NOT enabled")
            findings["checks"].append({
                "id": "encryption_at_rest",
                "title": "Encryption at rest",
                "status": "fail",
                "severity": "high",
                "finding": "Encryption at rest was not confirmed for data stores and snapshots.",
                "recommendation": "Enable service-native encryption with managed keys, then migrate or rotate unencrypted resources.",
            })

        if infrastructure.get("restrict_security_groups"):
            findings["passed"].append("✅ Security groups properly restricted")
            findings["checks"].append({
                "id": "security_groups",
                "title": "Security group exposure",
                "status": "pass",
                "severity": "informational",
                "finding": "Inbound and outbound rules are reported as restricted.",
                "recommendation": "Continuously detect public CIDRs, unused rules, and unexpected reachability.",
            })
        else:
            findings["warnings"].append("⚠️ Security groups may be too permissive")
            findings["checks"].append({
                "id": "security_groups",
                "title": "Security group exposure",
                "status": "warning",
                "severity": "high",
                "finding": "Restricted security group rules were not confirmed, increasing unintended network exposure risk.",
                "recommendation": "Remove broad public access, allow only required ports and sources, and enable flow-log monitoring.",
            })

        if infrastructure.get("mfa_enabled"):
            findings["passed"].append("✅ MFA enabled for admin access")
            findings["checks"].append({
                "id": "mfa",
                "title": "Administrative MFA",
                "status": "pass",
                "severity": "informational",
                "finding": "Administrative access is reported as protected by multi-factor authentication.",
                "recommendation": "Prefer phishing-resistant MFA and enforce it through the central identity provider.",
            })
        else:
            findings["failed"].append("❌ MFA NOT enabled (critical!)")
            findings["checks"].append({
                "id": "mfa",
                "title": "Administrative MFA",
                "status": "fail",
                "severity": "critical",
                "finding": "Multi-factor authentication was not confirmed for administrative access.",
                "recommendation": "Enforce MFA for privileged users immediately, centralize access with SSO, and secure emergency accounts.",
            })

        penalty = sum(
            SecurityScanner.CONTROL_WEIGHTS[check["id"]]
            for check in findings["checks"]
            if check["status"] != "pass"
        )
        score = max(0, 100 - penalty)
        if score >= 85:
            risk_level = "Low"
        elif score >= 65:
            risk_level = "Moderate"
        elif score >= 40:
            risk_level = "High"
        else:
            risk_level = "Critical"

        priority_count = sum(check["status"] != "pass" for check in findings["checks"])
        if priority_count:
            verb = "requires" if priority_count == 1 else "require"
            summary = (
                f"{priority_count} priority security gap{'s' if priority_count != 1 else ''} "
                f"{verb} action before this baseline should be considered production-ready."
            )
        else:
            summary = (
                "All three baseline controls are reported as enabled. Verify their implementation "
                "and broaden the review before treating the environment as production-ready."
            )

        findings.update({
            "score": score,
            "risk_level": risk_level,
            "summary": summary,
            "evaluated_checks": len(findings["checks"]),
            "passed_checks": len(findings["passed"]),
            "priority_actions": priority_count,
            "scope": (
                "Self-reported baseline of three controls. No cloud account, policy, logs, "
                "or resource configuration was inspected."
            ),
            "guidance_basis": "Cloud security fundamentals aligned with least-privilege and defense-in-depth practices.",
        })

        return findings


if __name__ == "__main__":
    print("UP2CLOUD Enhanced Features Module")
    print("=" * 60)
    
    # Test Cost Estimator
    print("\n1. Cost Estimation:")
    arch = {
        "ec2_instances": [
            {"type": "t3.medium", "count": 2},
            {"type": "m5.large", "count": 1}
        ],
        "rds_instances": [
            {"type": "db.m5.large"}
        ],
        "s3_storage_gb": 100
    }
    cost = CostEstimator.estimate_monthly_cost(arch)
    print(f"   Estimated Monthly Cost: ${cost['estimated_monthly_cost']}")
    print(f"   Breakdown: {cost['breakdown']}")
    
    # Test Code Generator
    print("\n2. Code Generation:")
    tf = CodeGenerator.generate_terraform(arch)
    print(f"   Generated Terraform config ({len(tf)} chars)")
    
    # Test Architecture Diagram
    print("\n3. Architecture Diagrams:")
    diagram = ArchitectureDiagrammer.generate_diagram("microservices")
    print(f"   Generated Mermaid diagram ({len(diagram)} chars)")
    
    # Test Conversation Memory
    print("\n4. Conversation Memory:")
    memory = ConversationMemory()
    memory.add_message("user", "How do we optimize costs?")
    memory.add_message("assistant", "Consider reserved instances...")
    print(f"   Session: {memory.session_id}")
    print(f"   History: {len(memory.conversation_history)} messages")
    
    # Test Security Scanner
    print("\n5. Security Scanning:")
    infra_with_security = {**arch, "encryption_enabled": True, "mfa_enabled": True}
    findings = SecurityScanner.scan_infrastructure(infra_with_security)
    print(f"   Security Score: {findings['score']:.1f}%")
    print(f"   Passed: {len(findings['passed'])}")
    print(f"   Failed: {len(findings['failed'])}")
