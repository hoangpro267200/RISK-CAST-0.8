# ☸️ RiskCast Kubernetes Deployment Guide

## Overview

Production-ready Kubernetes manifests for deploying RiskCast with high availability, security, and scalability.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│          Ingress Controller (Nginx)         │
│          SSL/TLS, Rate Limiting             │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐    ┌───────▼────────┐
│   API Pods     │    │  Worker Pods   │
│   (3-20)       │    │   (2-10)       │
│   + HPA        │    │   + HPA        │
└───────┬────────┘    └───────┬────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐    ┌───────▼────────┐
│   PostgreSQL   │    │     Redis      │
│   StatefulSet  │    │  StatefulSet   │
└────────────────┘    └────────────────┘
```

---

## Quick Start

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash

# Verify installation
kubectl version --client
kustomize version
```

### Deploy to Production

```bash
# 1. Build manifests
kustomize build k8s/overlays/production

# 2. Apply to cluster
kustomize build k8s/overlays/production | kubectl apply -f -

# 3. Check status
kubectl get pods -n riskcast-prod

# 4. Watch rollout
kubectl rollout status deployment/prod-riskcast-api -n riskcast-prod
```

### Using Helper Script

```bash
# Make executable
chmod +x scripts/k8s-deploy.sh

# Deploy
./scripts/k8s-deploy.sh deploy production

# Check status
./scripts/k8s-deploy.sh status production

# View logs
./scripts/k8s-deploy.sh logs production api
```

---

## Manifests

### Base Configuration (`k8s/base/`)

| File | Description | Resources |
|------|-------------|-----------|
| `namespace.yaml` | Namespace definition | 1 Namespace |
| `configmap.yaml` | Application configuration | 1 ConfigMap |
| `secret.yaml` | Sensitive configuration | 1 Secret |
| `serviceaccount.yaml` | Service accounts & RBAC | 2 ServiceAccounts, 2 Roles, 2 RoleBindings |
| `deployment.yaml` | API & Worker deployments | 2 Deployments |
| `service.yaml` | Service definitions | 2 Services |
| `ingress.yaml` | External access | 1 Ingress |
| `hpa.yaml` | Autoscaling configuration | 2 HPAs |
| `pdb.yaml` | Disruption budgets | 2 PDBs |

### Overlays

```
k8s/overlays/
├── development/     # Dev environment (1 replica, debug enabled)
├── staging/         # Staging environment (2 replicas, moderate resources)
└── production/      # Production environment (5 replicas, high resources)
```

---

## Configuration

### Environment Variables

**ConfigMap (`riskcast-config`):**
```yaml
ENVIRONMENT: "production"
LOG_LEVEL: "INFO"
API_PORT: "8000"
API_WORKERS: "4"
ENABLE_SWAGGER: "false"
ENABLE_METRICS: "true"
```

**Secret (`riskcast-secrets`):**
```yaml
DATABASE_URL: "postgresql://..."
REDIS_URL: "redis://..."
SECRET_KEY: "..."
AWS_ACCESS_KEY_ID: "..."
```

### Resource Limits

#### API Deployment (Production)

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 500m | 2000m |
| Memory | 1Gi | 4Gi |
| Replicas | 5 (min) | 30 (max) |

#### Worker Deployment (Production)

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 200m | 1000m |
| Memory | 512Mi | 2Gi |
| Replicas | 3 (min) | 15 (max) |

---

## Security Features

### 1. Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

### 2. Container Security

```yaml
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

### 3. RBAC

- Dedicated ServiceAccounts for API and Worker
- Minimal permissions (ConfigMaps, Secrets read-only)
- No cluster-wide access

### 4. Network Policies (Optional)

Create network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: riskcast-api-netpol
  namespace: riskcast-prod
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: riskcast-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
```

---

## High Availability

### 1. Pod Disruption Budgets

Ensures minimum availability during voluntary disruptions:

```yaml
minAvailable: 2  # For API
minAvailable: 1  # For Worker
```

### 2. Pod Anti-Affinity

Spreads pods across nodes and zones:

```yaml
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: riskcast-api
        topologyKey: kubernetes.io/hostname
```

### 3. Topology Spread

Balances pods across availability zones:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
```

---

## Autoscaling

### Horizontal Pod Autoscaler (HPA)

**API HPA:**
- Min: 3 replicas
- Max: 20 replicas
- Metrics: CPU 70%, Memory 80%

**Worker HPA:**
- Min: 2 replicas
- Max: 10 replicas
- Metrics: CPU 70%, Memory 75%

**Scaling Behavior:**

```yaml
scaleUp:
  stabilizationWindowSeconds: 0
  policies:
    - type: Percent
      value: 100
      periodSeconds: 15
    - type: Pods
      value: 4
      periodSeconds: 15

scaleDown:
  stabilizationWindowSeconds: 300
  policies:
    - type: Percent
      value: 10
      periodSeconds: 60
```

---

## Health Checks

### Liveness Probe

Detects if container is alive:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

### Readiness Probe

Detects if container is ready for traffic:

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: http
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

### Startup Probe

Detects if container has started:

```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: http
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 30
```

---

## Ingress Configuration

### TLS/SSL

```yaml
tls:
  - hosts:
      - api.riskcast.io
    secretName: riskcast-api-tls
```

### Rate Limiting

```yaml
annotations:
  nginx.ingress.kubernetes.io/limit-rps: "100"
  nginx.ingress.kubernetes.io/limit-connections: "50"
```

### CORS

```yaml
annotations:
  nginx.ingress.kubernetes.io/enable-cors: "true"
  nginx.ingress.kubernetes.io/cors-allow-origin: "https://app.riskcast.io"
```

### Security Headers

```yaml
annotations:
  nginx.ingress.kubernetes.io/configuration-snippet: |
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
```

---

## Secrets Management

### Option 1: Sealed Secrets

```bash
# Install Sealed Secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Seal a secret
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml
```

### Option 2: External Secrets Operator

```bash
# Install External Secrets
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Create SecretStore
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: riskcast-prod
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: riskcast-api
EOF
```

---

## Monitoring

### Prometheus Integration

Pods are annotated for Prometheus scraping:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

### ServiceMonitor (if using Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: riskcast-api
  namespace: riskcast-prod
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: riskcast-api
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

---

## Deployment Strategies

### Rolling Update (Default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### Blue-Green Deployment

```bash
# 1. Deploy new version with different label
kubectl apply -f deployment-v2.yaml

# 2. Wait for new pods to be ready
kubectl wait --for=condition=available --timeout=300s deployment/riskcast-api-v2

# 3. Switch service to new version
kubectl patch service riskcast-api -p '{"spec":{"selector":{"version":"v2"}}}'

# 4. Monitor and rollback if needed
kubectl patch service riskcast-api -p '{"spec":{"selector":{"version":"v1"}}}'
```

### Canary Deployment

```yaml
# Deploy canary with fewer replicas
apiVersion: apps/v1
kind: Deployment
metadata:
  name: riskcast-api-canary
spec:
  replicas: 1  # 10% of traffic
  # ... same spec as main deployment
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n riskcast-prod

# Check logs
kubectl logs <pod-name> -n riskcast-prod

# Check previous logs (if crashed)
kubectl logs <pod-name> -n riskcast-prod --previous
```

### Connection Issues

```bash
# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- sh
curl http://riskcast-api.riskcast-prod.svc.cluster.local

# Check endpoints
kubectl get endpoints riskcast-api -n riskcast-prod
```

### Resource Issues

```bash
# Check node resources
kubectl top nodes

# Check pod resources
kubectl top pods -n riskcast-prod

# Describe node
kubectl describe node <node-name>
```

---

## Commands Reference

### Deployment

```bash
# Deploy
kustomize build k8s/overlays/production | kubectl apply -f -

# Update image
kubectl set image deployment/prod-riskcast-api api=ghcr.io/riskcast/api:v1.1.0 -n riskcast-prod

# Rollback
kubectl rollout undo deployment/prod-riskcast-api -n riskcast-prod

# Check rollout status
kubectl rollout status deployment/prod-riskcast-api -n riskcast-prod

# Scale manually
kubectl scale deployment/prod-riskcast-api --replicas=10 -n riskcast-prod
```

### Debugging

```bash
# Get pods
kubectl get pods -n riskcast-prod

# Describe pod
kubectl describe pod <pod-name> -n riskcast-prod

# Logs
kubectl logs -f <pod-name> -n riskcast-prod

# Execute command in pod
kubectl exec -it <pod-name> -n riskcast-prod -- /bin/bash

# Port forward
kubectl port-forward <pod-name> 8000:8000 -n riskcast-prod
```

### Monitoring

```bash
# Watch pods
kubectl get pods -n riskcast-prod -w

# Resource usage
kubectl top pods -n riskcast-prod
kubectl top nodes

# Events
kubectl get events -n riskcast-prod --sort-by='.lastTimestamp'
```

---

**Version:** 1.0.0  
**Date:** 2026-01-24  
**Status:** ✅ Production Ready
