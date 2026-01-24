# Kubernetes Manifests

This directory contains Kubernetes manifests for deploying RISKCAST V3 to a Kubernetes cluster.

## File Structure

```
k8s/
├── namespace.yaml              # Namespace definition
├── configmap.yaml              # Application configuration
├── secrets.yaml.example        # Secrets template (copy to secrets.yaml)
├── service-account.yaml        # Service accounts for pods
├── mysql-deployment.yaml       # MySQL StatefulSet (optional)
├── redis-deployment.yaml       # Redis StatefulSet (optional)
├── migration-job.yaml          # Database migration job
├── api-deployment.yaml         # API deployment, service, and HPA
├── worker-deployment.yaml      # Worker deployment and HPA
├── ingress.yaml                # Ingress configuration
├── network-policy.yaml          # Network security policies
├── kustomization.yaml          # Kustomize configuration
├── KUBERNETES.md               # Detailed deployment guide
└── README.md                   # This file
```

## Quick Deploy

### Using kubectl

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Create secrets (edit first!)
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your values
kubectl apply -f secrets.yaml

# 3. Create configmap
kubectl apply -f configmap.yaml

# 4. Create service accounts
kubectl apply -f service-account.yaml

# 5. Deploy database (if using in-cluster)
kubectl apply -f mysql-deployment.yaml
kubectl apply -f redis-deployment.yaml

# 6. Run migrations
kubectl apply -f migration-job.yaml
kubectl wait --for=condition=complete job/riskcast-migrations --timeout=300s

# 7. Deploy application
kubectl apply -f api-deployment.yaml
kubectl apply -f worker-deployment.yaml

# 8. Configure ingress
kubectl apply -f ingress.yaml

# 9. Apply network policies
kubectl apply -f network-policy.yaml
```

### Using Kustomize

```bash
# Build and apply
kubectl apply -k .

# Or with specific environment
kubectl apply -k overlays/production
```

## Configuration

### Secrets

Copy `secrets.yaml.example` to `secrets.yaml` and update:

```bash
# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32)

# Update secrets.yaml
```

### ConfigMap

Edit `configmap.yaml` to adjust:
- Log levels
- Worker counts
- Database pool settings
- CORS origins

### Image

Update image references in deployments:
- `riskcast-api:latest` → `your-registry/riskcast-api:v1.0.0`

## Features

- ✅ **Namespace Isolation**: All resources in `riskcast` namespace
- ✅ **Health Checks**: Liveness and readiness probes
- ✅ **Auto-scaling**: HPA for API (3-10) and Worker (2-8)
- ✅ **Rolling Updates**: Zero-downtime deployments
- ✅ **Security**: Network policies, non-root containers, RBAC
- ✅ **TLS**: Ingress with cert-manager integration
- ✅ **Migrations**: Pre-deployment migration job
- ✅ **Monitoring**: Prometheus annotations

## See Also

- [KUBERNETES.md](./KUBERNETES.md) - Detailed deployment guide
- [../DOCKER.md](../DOCKER.md) - Docker deployment guide
- [../DEPLOYMENT.md](../DEPLOYMENT.md) - General deployment docs
