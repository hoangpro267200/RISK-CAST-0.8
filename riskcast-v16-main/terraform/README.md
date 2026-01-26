# Terraform Infrastructure as Code

This directory contains Terraform configurations for deploying RiskCast V16 to AWS.

## Directory Structure

```
terraform/
├── environments/          # Environment-specific configurations
│   ├── dev/              # Development environment
│   ├── staging/          # Staging environment
│   └── prod/             # Production environment
├── modules/              # Reusable Terraform modules
│   ├── vpc/             # VPC and networking
│   ├── eks/             # EKS cluster and node groups
│   ├── rds/             # RDS PostgreSQL
│   ├── elasticache/     # ElastiCache Redis
│   ├── s3/              # S3 buckets
│   └── secrets/         # Secrets Manager
├── main.tf              # Main configuration
├── variables.tf          # Root variables
├── outputs.tf            # Root outputs
└── versions.tf          # Provider versions
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0 installed
3. **S3 bucket** for Terraform state (create manually first)
4. **DynamoDB table** for state locking (create manually first)

## Initial Setup

### 1. Create S3 Backend for State

```bash
aws s3api create-bucket \
  --bucket riskcast-terraform-state \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

aws s3api put-bucket-versioning \
  --bucket riskcast-terraform-state \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket riskcast-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 2. Create DynamoDB Table for State Locking

```bash
aws dynamodb create-table \
  --table-name riskcast-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

## Usage

### Development Environment

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### Staging Environment

```bash
cd terraform/environments/staging
terraform init
terraform plan
terraform apply
```

### Production Environment

```bash
cd terraform/environments/prod
terraform init
terraform plan  # Review carefully!
terraform apply
```

## Infrastructure Components

### VPC Module
- VPC with DNS support
- Public subnets (for load balancers)
- Private subnets (for EKS nodes)
- Database subnets (for RDS)
- NAT Gateways (one per AZ)
- Internet Gateway
- Route tables and associations
- Subnet groups for RDS and ElastiCache

### EKS Module
- EKS cluster with managed control plane
- Managed node groups with auto-scaling
- IAM roles for cluster and nodes
- OIDC provider for IRSA (IAM Roles for Service Accounts)
- Security groups
- CloudWatch logging enabled

### RDS Module
- PostgreSQL 15.4 database
- Multi-AZ support (configurable)
- Automated backups
- Performance Insights
- Parameter group with optimized settings
- Secrets Manager integration
- Encrypted storage

### ElastiCache Module
- Redis 7.0 cluster
- Multi-AZ with automatic failover
- Encryption at rest and in transit
- Auth token enabled
- Secrets Manager integration

### S3 Module
- Logs bucket (90-day retention)
- Data bucket (versioned, encrypted)
- Backups bucket (lifecycle to Glacier)

### Secrets Module
- Centralized secrets management
- Integration with RDS and Redis

## Environment Differences

| Component | Dev | Staging | Prod |
|-----------|-----|---------|------|
| EKS Nodes | 2 (t3.large) | 3 (t3.xlarge) | 5 (m6i.xlarge) |
| RDS Instance | db.t4g.medium | db.r6g.large | db.r6g.xlarge |
| RDS Storage | 20GB | 100GB | 200GB |
| RDS Multi-AZ | No | No | Yes |
| Redis Nodes | 1 (t4g.micro) | 2 (r6g.medium) | 3 (r6g.large) |
| Backup Retention | 3 days | 7 days | 35 days |

## Security Features

- **Encryption**: All data encrypted at rest and in transit
- **Network Isolation**: Private subnets for compute and database
- **IAM Roles**: Least privilege access with IRSA
- **Secrets Manager**: Secure credential storage
- **Security Groups**: Restrictive firewall rules
- **VPC**: Isolated network environment

## Cost Optimization

- **Dev**: Minimal resources, single AZ
- **Staging**: Moderate resources, no Multi-AZ
- **Prod**: Full redundancy, Multi-AZ, larger instances

## Outputs

After deployment, Terraform outputs:
- VPC ID
- EKS cluster endpoint and name
- RDS endpoint
- Redis endpoint
- S3 bucket names

## Destroying Infrastructure

⚠️ **Warning**: This will delete all resources!

```bash
cd terraform/environments/{env}
terraform destroy
```

## Troubleshooting

### State Lock Issues
If Terraform is stuck with a lock:
```bash
aws dynamodb delete-item \
  --table-name riskcast-terraform-locks \
  --key '{"LockID": {"S": "..."}}'
```

### Module Not Found
Ensure you're running `terraform init` in the environment directory.

### Provider Version Issues
Check `versions.tf` for required provider versions.

## Next Steps

After infrastructure is deployed:
1. Configure kubectl to connect to EKS cluster
2. Deploy application using Kubernetes manifests
3. Configure DNS and load balancers
4. Set up monitoring and alerting
5. Configure CI/CD pipelines
