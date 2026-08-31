# UP2CLOUD AI Engineering Assistant Model

Complete Baseten model implementation for UP2CLOUD's AI-powered cloud engineering and technology consulting assistant.

## Overview

This model provides a conversational AI assistant specialized in:
- **Cloud Architecture**: AWS, GCP, Azure design patterns and best practices
- **Platform Engineering**: Kubernetes, container orchestration, DevOps practices
- **Infrastructure as Code**: Terraform, CloudFormation, Pulumi
- **FinOps**: Cost optimization, billing management, resource efficiency
- **AI-powered Operations**: MLOps, monitoring, automation

## Project Structure

```
baseten/
├── model.py              # Main model implementation with inference logic
├── baseten_config.py     # Baseten deployment configuration
├── deploy.py             # Deployment script
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── tests/                # (Optional) Unit tests
    └── test_model.py
```

## Model Capabilities

### Input Format
```json
{
  "prompt": "How can we optimize our AWS costs for variable workloads?",
  "context": {
    "company_type": "startup",
    "current_infrastructure": "EC2 + RDS on AWS",
    "challenges": "High monthly bills",
    "budget_constraints": "Need 30% cost reduction",
    "timeline": "3 months"
  }
}
```

### Output Format
```json
{
  "response": "Technical advice and recommendations...",
  "model": "up2cloud-engineering-assistant",
  "usage": {
    "input_tokens": 42,
    "output_tokens": 156
  },
  "confidence": 0.95,
  "references": ["AWS Cost Optimization", "Reserved Instances", "Spot Instances"]
}
```

## Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Set Baseten API key
export BASETEN_API_KEY="czrVhIYe.BOIiYx2wopD1DAKc5LTIalcLZ7yRHSF5"
```

### 2. Test Locally
```bash
python deploy.py test
```

### 3. Deploy to Baseten
```bash
# Install Baseten CLI
pip install baseten

# Deploy the model
python deploy.py
```

## API Endpoints

Once deployed, the model is available as a REST API:

### Predict Endpoint
```
POST /v1/models/up2cloud-engineering-assistant/predict
```

**Example Request:**
```bash
curl -X POST https://baseten.co/api/v1/predict \
  -H "Authorization: Api-Key YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How should we migrate to Kubernetes?",
    "context": {
      "company_type": "SaaS",
      "current_infrastructure": "Traditional VM setup"
    }
  }'
```

## Integration Points

### Supported Cloud Providers
- **AWS**: EC2, S3, Lambda, RDS, CloudFormation, Cost Explorer API
- **Google Cloud**: Compute Engine, GKE, Cloud Run, BigQuery
- **Microsoft Azure**: VMs, AKS, Cosmos DB, Azure DevOps

### IaC Frameworks
- Terraform
- CloudFormation
- Pulumi
- Helm charts for Kubernetes

### DevOps Tools
- Kubernetes (EKS, GKE, AKS)
- Docker & Container registries
- CI/CD (GitHub Actions, GitLab CI, Jenkins, ArgoCD)
- Monitoring (Prometheus, Grafana, DataDog, CloudWatch)

## Configuration

Edit `baseten_config.py` to customize:
- Model name and description
- Input/output schemas
- Runtime resources (memory, timeout, concurrency)
- Model metadata and tags

## Performance

- **Latency**: ~2-5 seconds for typical queries
- **Concurrency**: 10 concurrent requests
- **Memory**: 2GB runtime environment
- **Timeout**: 60 seconds per request

## Monitoring

The model tracks:
- Request latency
- Throughput (requests/sec)
- Error rates
- Token usage (input/output)

View metrics in Baseten dashboard after deployment.

## Example Queries

### 1. Cost Optimization
```
"How can we reduce our monthly AWS bill from $15K to $10K?"
```

### 2. Kubernetes Migration
```
"We're running monolithic apps on EC2. How do we transition to Kubernetes?"
```

### 3. FinOps Implementation
```
"What FinOps best practices should a startup implement?"
```

### 4. Multi-Cloud Strategy
```
"Should we adopt a multi-cloud strategy? Pros and cons?"
```

### 5. Security & Compliance
```
"How do we ensure our infrastructure is compliant with SOC2?"
```

## Next Steps

1. Deploy the model to Baseten using the API key provided
2. Test with sample queries
3. Integrate the model API into UP2CLOUD's website/portal
4. Monitor usage and performance in Baseten dashboard
5. Iterate on the system prompt based on user feedback

## Support

For questions or issues:
- Check Baseten documentation: https://docs.baseten.co/
- Review the model code in `model.py`
- Test locally using `python deploy.py test`

---

**Model ID**: `up2cloud-engineering-assistant`  
**Version**: 1.0.0  
**Status**: Ready for deployment
