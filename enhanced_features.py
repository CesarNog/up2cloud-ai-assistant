"""
UP2CLOUD Model - Enhanced Features Module
Adds cost estimation, code generation, architecture diagramming, and more.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


class CostEstimator:
    """Validated AWS cost baseline with explicit pricing provenance."""
    
    AWS_PRICING = {
        "ec2": {
            "t3.medium": 0.0418,  # per hour, on-demand; AWS us-east-1 reviewed 2026-08-31
            "t3.large": 0.0835,
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

    PRICING_METADATA = {
        "provider": "AWS",
        "region": "us-east-1",
        "currency": "USD",
        "rate_type": "public on-demand Linux baseline",
        "catalog_version": "2026-08-31",
        "last_reviewed": "2026-08-31",
        "sources": [
            "https://aws.amazon.com/ec2/pricing/on-demand/",
            "https://aws.amazon.com/rds/pricing/",
            "https://aws.amazon.com/s3/pricing/",
            "https://aws.amazon.com/lambda/pricing/",
        ],
        "disclaimer": "Indicative catalog for comparison; confirm final prices in the AWS Pricing Calculator before commitment.",
    }
    
    @staticmethod
    def estimate_monthly_cost(infrastructure: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate a monthly baseline and optimization scenarios."""
        if not isinstance(infrastructure, dict):
            raise ValueError("Infrastructure must be an object")

        region = infrastructure.get("region", "us-east-1")
        if region != "us-east-1":
            raise ValueError("The current verified pricing catalog supports us-east-1 only")

        total_cost = 0
        breakdown = {}
        unknown_rates = []
        
        # EC2 estimation
        if "ec2_instances" in infrastructure:
            ec2_cost = 0
            for instance in infrastructure["ec2_instances"]:
                instance_type = instance.get("type", "t3.medium")
                count = instance.get("count", 1)
                hours = instance.get("monthly_hours", 730)
                if instance_type not in CostEstimator.AWS_PRICING["ec2"]:
                    unknown_rates.append(f"EC2 {instance_type}")
                    continue
                if count < 0 or hours < 0:
                    raise ValueError("EC2 count and monthly hours must be non-negative")
                hourly_rate = CostEstimator.AWS_PRICING["ec2"][instance_type]
                monthly_cost = hourly_rate * hours * count
                ec2_cost += monthly_cost
            breakdown["EC2"] = ec2_cost
            total_cost += ec2_cost
        
        # RDS estimation
        if "rds_instances" in infrastructure:
            rds_cost = 0
            for db in infrastructure["rds_instances"]:
                db_type = db.get("type", "db.t3.micro")
                count = db.get("count", 1)
                hours = db.get("monthly_hours", 730)
                if db_type not in CostEstimator.AWS_PRICING["rds"]:
                    unknown_rates.append(f"RDS {db_type}")
                    continue
                if count < 0 or hours < 0:
                    raise ValueError("RDS count and monthly hours must be non-negative")
                hourly_rate = CostEstimator.AWS_PRICING["rds"][db_type]
                monthly_cost = hourly_rate * hours * count
                rds_cost += monthly_cost
            breakdown["RDS"] = rds_cost
            total_cost += rds_cost
        
        # S3 estimation
        if "s3_storage_gb" in infrastructure:
            storage_gb = infrastructure["s3_storage_gb"]
            if storage_gb < 0:
                raise ValueError("S3 storage must be non-negative")
            s3_cost = storage_gb * CostEstimator.AWS_PRICING["s3"]["storage_gb"]
            breakdown["S3"] = s3_cost
            total_cost += s3_cost
        
        # Lambda estimation
        if "lambda_requests" in infrastructure:
            lambda_requests = infrastructure["lambda_requests"]
            if lambda_requests < 0:
                raise ValueError("Lambda requests must be non-negative")
            lambda_cost = (lambda_requests / 1_000_000) * CostEstimator.AWS_PRICING["lambda"]["per_million_requests"]
            breakdown["Lambda"] = lambda_cost
            total_cost += lambda_cost
        
        total_cost = round(total_cost, 2)
        compute_database = breakdown.get("EC2", 0) + breakdown.get("RDS", 0)
        other_services = total_cost - compute_database
        commitment_total = round((compute_database * 0.70) + other_services, 2)
        scheduled_total = round((compute_database * 0.55) + other_services, 2)

        evidence = infrastructure.get("evidence") or {}
        observed_spend = evidence.get("observed_monthly_spend")
        utilization = evidence.get("average_compute_utilization_percent")
        evidence_items = sum(value is not None for value in (observed_spend, utilization))
        confidence = "high" if evidence_items == 2 else "medium" if evidence_items == 1 else "baseline"

        scenarios = [
            {
                "id": "on_demand",
                "name": "On-demand baseline",
                "monthly_cost": total_cost,
                "savings": 0,
                "assumption": "Selected resources run for the entered monthly hours at the reviewed public rates.",
            },
            {
                "id": "commitment_optimized",
                "name": "Commitment-optimized scenario",
                "monthly_cost": commitment_total,
                "savings": round(total_cost - commitment_total, 2),
                "assumption": "Illustrative 30% compute/database reduction after rightsizing; not a commercial quote.",
            },
            {
                "id": "scheduled_nonproduction",
                "name": "Scheduled non-production scenario",
                "monthly_cost": scheduled_total,
                "savings": round(total_cost - scheduled_total, 2),
                "assumption": "Illustrative 45% compute/database reduction for workloads that can be stopped or scaled down.",
            },
        ]

        observed_variance = None
        if observed_spend is not None:
            observed_variance = {
                "observed_monthly_spend": round(observed_spend, 2),
                "difference": round(observed_spend - total_cost, 2),
                "explanation": "A variance can represent omitted services, discounts, taxes, data transfer, or different utilization.",
            }

        return {
            "estimated_monthly_cost": total_cost,
            "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
            "currency": "USD",
            "period": "monthly",
            "estimate_range": {
                "low": round(total_cost * 0.90, 2),
                "high": round(total_cost * 1.15, 2),
            },
            "scenarios": scenarios,
            "observed_variance": observed_variance,
            "evidence": {
                "confidence": confidence,
                "source": evidence.get("evidence_source") or "user-entered workload profile",
                "average_compute_utilization_percent": utilization,
            },
            "pricing_metadata": dict(CostEstimator.PRICING_METADATA),
            "warnings": [f"No reviewed catalog rate was available for {name}." for name in unknown_rates],
        }


class CodeGenerator:
    """Generate Infrastructure as Code templates."""
    
    @staticmethod
    def generate_terraform(architecture: Dict[str, Any]) -> str:
        """Generate a secure Terraform starter while preserving the legacy string API."""

        requirement = architecture.get("requirement") or architecture.get("requirements") or "Secure AWS platform foundation"
        return CodeGenerator.generate_terraform_bundle(requirement, architecture)["combined_code"]

    @staticmethod
    def generate_terraform_bundle(requirement: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Generate a multi-file, secure-by-default AWS foundation and validate it."""

        context = context or {}
        aws_region = context.get("aws_region", "us-east-1")
        normalized = requirement.lower()
        if "eks" in normalized or "kubernetes" in normalized:
            profile = "eks_foundation"
            profile_name = "Amazon EKS platform foundation"
        elif "serverless" in normalized or "lambda" in normalized:
            profile = "serverless_foundation"
            profile_name = "AWS serverless platform foundation"
        elif "three-tier" in normalized or "fargate" in normalized or "ecs" in normalized:
            profile = "three_tier_foundation"
            profile_name = "Three-tier AWS platform foundation"
        else:
            profile = "network_foundation"
            profile_name = "Secure AWS network foundation"

        files = [
            {
                "name": "versions.tf",
                "language": "hcl",
                "content": '''terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
''',
            },
            {
                "name": "variables.tf",
                "language": "hcl",
                "content": f'''variable "aws_region" {{
  description = "AWS region for the platform foundation"
  type        = string
  default     = "{aws_region}"
}}

variable "environment" {{
  description = "Deployment environment"
  type        = string
  default     = "production"

  validation {{
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }}
}}

variable "allowed_ingress_cidrs" {{
  description = "Explicit trusted CIDRs permitted to reach the application on TLS; empty by default"
  type        = list(string)
  default     = []
}}
''',
            },
            {
                "name": "main.tf",
                "language": "hcl",
                "content": f'''locals {{
  workload_profile = "{profile}"
  common_tags = {{
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "platform-engineering"
    Service     = "up2cloud-demo-foundation"
  }}
}}

provider "aws" {{
  region = var.aws_region

  default_tags {{
    tags = local.common_tags
  }}
}}

data "aws_availability_zones" "available" {{
  state = "available"
}}

resource "aws_vpc" "main" {{
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{ Name = "up2cloud-${{var.environment}}-vpc" }}
}}

resource "aws_subnet" "private" {{
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 4, count.index)
  map_public_ip_on_launch = false

  tags = {{ Name = "up2cloud-${{var.environment}}-private-${{count.index + 1}}" }}
}}

resource "aws_security_group" "application" {{
  name_prefix = "up2cloud-${{var.environment}}-app-"
  description = "TLS access from explicitly trusted network ranges"
  vpc_id      = aws_vpc.main.id

  dynamic "ingress" {{
    for_each = length(var.allowed_ingress_cidrs) > 0 ? [1] : []
    content {{
      description = "TLS from approved CIDRs"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = var.allowed_ingress_cidrs
    }}
  }}
}}

resource "aws_kms_key" "data" {{
  description             = "Customer-managed key for ${{local.workload_profile}} data"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}}

resource "aws_s3_bucket" "audit" {{
  bucket_prefix = "up2cloud-${{var.environment}}-audit-"
  force_destroy = false
}}

resource "aws_s3_bucket_public_access_block" "audit" {{
  bucket = aws_s3_bucket.audit.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit" {{
  bucket = aws_s3_bucket.audit.id

  rule {{
    apply_server_side_encryption_by_default {{
      kms_master_key_id = aws_kms_key.data.arn
      sse_algorithm     = "aws:kms"
    }}
  }}
}}

resource "aws_s3_bucket_versioning" "audit" {{
  bucket = aws_s3_bucket.audit.id
  versioning_configuration {{ status = "Enabled" }}
}}
''',
            },
            {
                "name": "outputs.tf",
                "language": "hcl",
                "content": '''output "vpc_id" {
  description = "Platform VPC identifier"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet identifiers across three availability zones"
  value       = aws_subnet.private[*].id
}

output "application_security_group_id" {
  description = "Security group with deny-by-default ingress"
  value       = aws_security_group.application.id
}
''',
            },
        ]

        combined_code = "\n".join(
            f"# --- {file['name']} ---\n{file['content'].strip()}\n"
            for file in files
            if file["language"] == "hcl"
        )
        validation = TerraformValidator.validate(combined_code)
        return {
            "profile": profile,
            "profile_name": profile_name,
            "requirement": requirement,
            "files": files,
            "combined_code": combined_code,
            "validation": validation,
            "generation_notice": (
                "Secure reviewable foundation generated from a bounded template. Application-specific resources, "
                "state configuration, IAM permissions, and deployment testing still require expert review."
            ),
        }

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


class TerraformValidator:
    """Static safety validation for generated Terraform starter files."""

    CHECKS = (
        ("no_public_cidr", "No public IPv4 allow-all CIDR", lambda code: "0.0.0.0/0" not in code),
        ("provider_pinned", "AWS provider version is constrained", lambda code: 'version = "~> 5.0"' in code),
        ("terraform_pinned", "Terraform version is constrained", lambda code: "required_version" in code),
        ("private_subnets", "Subnets disable public IP assignment", lambda code: "map_public_ip_on_launch = false" in code),
        ("encryption", "Customer-managed encryption and rotation are enabled", lambda code: "enable_key_rotation" in code and "aws:kms" in code),
        ("public_access_block", "S3 public access is blocked", lambda code: "restrict_public_buckets = true" in code),
        ("default_tags", "Provider-level ownership tags are configured", lambda code: "default_tags" in code and "ManagedBy" in code),
    )

    @staticmethod
    def validate(code: str) -> Dict[str, Any]:
        results = [
            {"id": check_id, "title": title, "status": "pass" if test(code) else "fail"}
            for check_id, title, test in TerraformValidator.CHECKS
        ]
        failed = [check for check in results if check["status"] == "fail"]
        return {
            "status": "passed" if not failed else "failed",
            "engine": "up2cloud-static-iac-v1",
            "checks": results,
            "issues": [check["title"] for check in failed],
            "limitations": [
                "Static checks do not replace terraform validate against initialized providers.",
                "Generated infrastructure must be reviewed and tested in a non-production account.",
            ],
        }


class ArchitectureDiagrammer:
    """Generate Mermaid diagrams for architecture visualization."""

    METADATA = {
        "microservices": {
            "title": "AWS microservices reference pattern",
            "description": "Edge delivery, load balancing, independently deployable services, managed data, and centralized telemetry.",
            "components": ["CloudFront", "Application Load Balancer", "ECS services", "Aurora", "ElastiCache", "SQS", "CloudWatch"],
        },
        "serverless": {
            "title": "AWS serverless event-driven pattern",
            "description": "Managed API, function compute, durable storage, events, and asynchronous messaging.",
            "components": ["API Gateway", "Lambda", "DynamoDB", "S3", "SNS", "SQS", "EventBridge"],
        },
        "kubernetes": {
            "title": "Managed Kubernetes platform pattern",
            "description": "Ingress, service routing, stateless and stateful workloads, persistent storage, configuration, and registry integration.",
            "components": ["Load Balancer", "Ingress controller", "Deployments", "StatefulSet", "Services", "Persistent Volumes", "Container Registry"],
        },
    }

    @staticmethod
    def generate_architecture(architecture_type: str) -> Dict[str, Any]:
        """Return a diagram plus the metadata required for accessible rendering."""

        selected_type = architecture_type if architecture_type in ArchitectureDiagrammer.METADATA else "microservices"
        diagram = ArchitectureDiagrammer.generate_diagram(selected_type)
        for icon in ("👤", "👥", "🌐", "⚙️", "🔐", "📡", "🗄️", "⚡", "📦", "📊", "📈", "🔗", "📝", "🔄", "🪣", "📢", "📅", "📥", "🐳", "💾", "📋"):
            diagram = diagram.replace(icon, "")
        metadata = ArchitectureDiagrammer.METADATA[selected_type]
        return {
            "type": selected_type,
            "title": metadata["title"],
            "description": metadata["description"],
            "components": metadata["components"],
            "diagram": diagram.strip(),
            "format": "mermaid",
            "accessibility_summary": f"{metadata['title']}. {metadata['description']} Components: {', '.join(metadata['components'])}.",
        }
    
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
        """Assess self-reported controls and corroborate them with supplied evidence."""
        evidence_text = str(infrastructure.get("evidence_text") or "").lower()
        evidence_source = infrastructure.get("evidence_source", "self_reported")
        positive_signals = {
            "encryption_at_rest": [
                signal
                for signal in ("kms_key_id", "storage_encrypted", "server_side_encryption", "enable_key_rotation")
                if signal in evidence_text
            ],
            "mfa": [
                signal
                for signal in ("mfa_enabled", "multi_factor", "virtual_mfa_device", "phishing-resistant")
                if signal in evidence_text
            ],
            "security_groups": [
                signal
                for signal in ("security_group", "allowed_ingress_cidrs", "restricted_security_group")
                if signal in evidence_text
            ],
        }
        adverse_signals = {
            "security_groups": [signal for signal in ("0.0.0.0/0", "::/0") if signal in evidence_text],
        }

        encryption_enabled = bool(infrastructure.get("encryption_enabled") or positive_signals["encryption_at_rest"])
        mfa_enabled = bool(infrastructure.get("mfa_enabled") or positive_signals["mfa"])
        restricted_security_groups = bool(
            (infrastructure.get("restrict_security_groups") or positive_signals["security_groups"])
            and not adverse_signals["security_groups"]
        )
        findings = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "checks": [],
        }

        if encryption_enabled:
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

        if restricted_security_groups:
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

        if mfa_enabled:
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

        for check in findings["checks"]:
            signals = positive_signals.get(check["id"], [])
            adverse = adverse_signals.get(check["id"], [])
            if adverse:
                evidence_status = "adverse"
                evidence_signals = adverse
            elif signals and check["status"] == "pass":
                evidence_status = "verified"
                evidence_signals = signals
            elif check["status"] == "pass":
                evidence_status = "reported"
                evidence_signals = []
            else:
                evidence_status = "not_provided"
                evidence_signals = []
            check["evidence"] = {
                "status": evidence_status,
                "source": evidence_source,
                "signals": evidence_signals,
            }

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

        verified_checks = sum(
            check["evidence"]["status"] == "verified"
            for check in findings["checks"]
        )
        adverse_checks = sum(
            check["evidence"]["status"] == "adverse"
            for check in findings["checks"]
        )
        evidence_mode = bool(evidence_text.strip())
        if not priority_count and verified_checks:
            summary = (
                f"All three baseline controls are enabled, with {verified_checks} corroborated by supplied evidence. "
                "Broaden the review before treating the environment as production-ready."
            )

        findings.update({
            "score": score,
            "risk_level": risk_level,
            "summary": summary,
            "evaluated_checks": len(findings["checks"]),
            "passed_checks": len(findings["passed"]),
            "priority_actions": priority_count,
            "scope": (
                "Evidence-assisted baseline of three controls. Supplied text was pattern-checked; no live cloud account was accessed."
                if evidence_mode
                else "Self-reported baseline of three controls. No cloud account, policy, logs, or resource configuration was inspected."
            ),
            "evidence_summary": {
                "mode": "evidence_assisted" if evidence_mode else "self_reported",
                "source": evidence_source,
                "verified_checks": verified_checks,
                "adverse_checks": adverse_checks,
                "coverage_percent": round((verified_checks / len(findings["checks"])) * 100),
                "limitations": "Pattern matching is not a semantic Terraform plan or cloud-provider configuration audit.",
            },
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
