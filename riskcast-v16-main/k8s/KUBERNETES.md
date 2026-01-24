# Kubernetes Deployment Guide

This guide covers Kubernetes-based deployment for RISKCAST V3.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker image `riskcast-api:latest` available in your registry
- Ingress controller (nginx-ingress recommended)
- cert-manager (for TLS certificates)

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Create Secrets

```bash
# Copy and edit the secrets template
cp k8s/secrets.yaml.example k8s/secrets.yaml

# Edit secrets.yaml with your actual values
# Generate secrets:
# SECRET_KEY=$(openssl rand -hex 32)
# DB_PASSWORD=$(openssl rand -base64 32)

# Apply secrets
kubectl apply -f k8s/secrets.yaml
```

### 3. Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Create Service Accounts

```bash
kubectl apply -f k8s/service-account.yaml
```

### 5. Deploy Database (Optional - if not using external DB)

```bash
# MySQL
kubectl apply -f k8s/mysql-deployment.yaml

# Redis (optional)
kubectl apply -f k8s/redis-deployment.yaml
```

### 6. Run Migrations

```bash
kubectl apply -f k8s/migration-job.yaml

# Check migration status
kubectl get jobs -n riskcast
kubectl logs -n riskcast job/riskcast-migrations
```

### 7. Deploy Application

```bash
# API
kubectl apply -f k8s/api-deployment.yaml

# Worker
kubectl apply -f k8s/worker-deployment.yaml
```

### 8. Configure Ingress

```bash
kubectl apply -f k8s/ingress.yaml
```

### 9. Apply Network Policies

```bash
kubectl apply -f k8s/network-policy.yaml
```

## Verification

### Check Pods

```bash
kubectl get pods -n riskcast
```

### Check Services

```bash
kubectl get svc -n riskcast
```

### Check Ingress

```bash
kubectl get ingress -n riskcast
```

### Test Health Endpoint

```bash
# Port forward to test
kubectl port-forward -n riskcast svc/riskcast-api 8000:80

# Test health
curl http://localhost:8000/health
```

## Scaling

### Manual Scaling

```bash
# Scale API
kubectl scale deployment riskcast-api -n riskcast --replicas=5

# Scale Worker
kubectl scale deployment riskcast-worker -n riskcast --replicas=4
```

### Automatic Scaling (HPA)

HPA is already configured:
- API: 3-10 replicas based on CPU (70%) and memory (80%)
- Worker: 2-8 replicas based on CPU (80%) and memory (80%)

View HPA status:
```bash
kubectl get hpa -n riskcast
```

## Monitoring

### View Logs

```bash
# API logs
kubectl logs -n riskcast -l app=riskcast-api --tail=100 -f

# Worker logs
kubectl logs -n riskcast -l app=riskcast-worker --tail=100 -f
```

### Metrics

Prometheus annotations are configured. If Prometheus is installed:

```bash
# Check service discovery
kubectl get pods -n riskcast -o yaml | grep prometheus.io
```

## Updates and Rollouts

### Rolling Update

```bash
# Update image
kubectl set image deployment/riskcast-api -n riskcast api=riskcast-api:v1.2.0

# Watch rollout
kubectl rollout status deployment/riskcast-api -n riskcast

# Rollback if needed
kubectl rollout undo deployment/riskcast-api -n riskcast
```

### Run Migrations Before Update

```bash
# Delete old migration job
kubectl delete job riskcast-migrations -n riskcast

# Apply new migration job
kubectl apply -f k8s/migration-job.yaml

# Wait for completion
kubectl wait --for=condition=complete job/riskcast-migrations -n riskcast --timeout=300s
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n riskcast

# Check events
kubectl get events -n riskcast --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Check MySQL pod
kubectl logs -n riskcast -l app=mysql

# Test connection from API pod
kubectl exec -it -n riskcast deployment/riskcast-api -- python -c "from app.database import engine; engine.connect()"
```

### Worker Not Processing Jobs

```bash
# Check worker logs
kubectl logs -n riskcast -l app=riskcast-worker

# Check worker process
kubectl exec -it -n riskcast deployment/riskcast-worker -- ps aux | grep worker
```

### Network Policy Blocking

```bash
# Check network policies
kubectl get networkpolicies -n riskcast

# Temporarily disable for testing
kubectl delete networkpolicy riskcast-network-policy -n riskcast
```

## Backup and Restore

### Database Backup

```bash
# Create backup job
kubectl run mysql-backup --image=mysql:8.0 --rm -it --restart=Never -n riskcast -- \
  mysqldump -h mysql-service -u riskcast -p riskcast_v3 > backup.sql
```

### Database Restore

```bash
# Restore from backup
kubectl run mysql-restore --image=mysql:8.0 --rm -it --restart=Never -n riskcast -- \
  mysql -h mysql-service -u riskcast -p riskcast_v3 < backup.sql
```

## Security Best Practices

1. **Secrets Management**: Use external secret management (e.g., HashiCorp Vault, AWS Secrets Manager)
2. **Image Scanning**: Scan images for vulnerabilities before deployment
3. **Network Policies**: Network policies are enabled by default
4. **RBAC**: Service accounts have minimal permissions
5. **Non-root**: All containers run as non-root user (UID 1000)
6. **Read-only Filesystem**: Consider enabling where possible (currently disabled for logs)

## Resource Recommendations

### Production

- **API**: 3-10 replicas, 250m-1000m CPU, 512Mi-2Gi memory
- **Worker**: 2-8 replicas, 500m-2000m CPU, 1Gi-4Gi memory
- **MySQL**: 1 replica (consider HA setup), 500m-2000m CPU, 1Gi-2Gi memory
- **Redis**: 1 replica, 100m-500m CPU, 256Mi-512Mi memory

### Development

- **API**: 1 replica, 100m CPU, 256Mi memory
- **Worker**: 1 replica, 200m CPU, 512Mi memory

## External Dependencies

If using external services instead of in-cluster:

1. **External MySQL**: Update `DATABASE_URL` in secrets
2. **External Redis**: Update `REDIS_URL` in secrets
3. **Remove**: MySQL and Redis deployments

## Cleanup

```bash
# Delete all resources
kubectl delete namespace riskcast

# Or delete individually
kubectl delete -f k8s/
```
