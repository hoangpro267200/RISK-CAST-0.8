# CI/CD Pipeline Guide

## 📚 Table of Contents

- [Overview](#overview)
- [CI Pipeline](#ci-pipeline)
- [CD Pipeline](#cd-pipeline)
- [ArgoCD Setup](#argocd-setup)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

Complete CI/CD pipeline with GitHub Actions for continuous integration and ArgoCD for continuous deployment.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   GitHub Repository                       │
│  - Code push/PR                                           │
│  - Triggers CI pipeline                                   │
└──────────────────────────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│              CI Pipeline (GitHub Actions)                 │
│  1. Code Quality (ruff, black, mypy)                      │
│  2. Unit Tests (pytest, coverage)                         │
│  3. Integration Tests (postgres, redis)                   │
│  4. Security Scan (bandit, safety, trivy)                 │
│  5. Build Docker Image                                    │
│  6. Push to Registry (GHCR)                               │
└──────────────────────────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│              CD Pipeline (GitHub Actions)                 │
│  - Deploy to Staging (main branch)                        │
│  - Deploy to Production (tags)                            │
│  - Run smoke tests                                        │
│  - Send notifications                                     │
└──────────────────────────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│                 ArgoCD (GitOps)                           │
│  - Monitors Git repository                                │
│  - Auto-syncs Kubernetes manifests                        │
│  - Self-healing                                           │
│  - Rollback capability                                    │
└──────────────────────────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│              Kubernetes Cluster                           │
│  - Staging namespace                                      │
│  - Production namespace                                   │
└──────────────────────────────────────────────────────────┘
```

---

## 🔄 CI Pipeline

### Workflow: `.github/workflows/ci.yml`

Runs on:
- Push to `main`, `develop`, `feature/*`, `release/*`
- Pull requests to `main`, `develop`

### Jobs

#### 1. Code Quality

```yaml
Tools:
  - ruff: Fast Python linter
  - black: Code formatter
  - isort: Import sorter
  - mypy: Type checker
```

**Example run:**
```bash
# Locally test what CI will run
ruff check . --output-format=github
black --check --diff .
isort --check-only --diff .
mypy app/ --ignore-missing-imports
```

#### 2. Unit Tests

```yaml
Features:
  - pytest with coverage
  - Parallel execution (-n auto)
  - Coverage threshold: 70%
  - Upload to Codecov
```

**Example run:**
```bash
pytest tests/unit/ \
  -v \
  --cov=app \
  --cov-report=xml \
  --cov-fail-under=70 \
  -n auto
```

#### 3. Integration Tests

```yaml
Services:
  - PostgreSQL 15
  - Redis 7
  
Features:
  - Alembic migrations
  - Database seeding
  - API testing
```

**Example run:**
```bash
# Start services with docker-compose
docker-compose -f docker-compose.test.yml up -d

# Run tests
export DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/riskcast_test
export REDIS_URL=redis://localhost:6379
pytest tests/integration/ -v
```

#### 4. Security Scan

```yaml
Tools:
  - bandit: Python code security
  - safety: Dependency vulnerabilities
  - pip-audit: Package auditing
```

**Reports:**
- `bandit-report.json`
- `safety-report.json`
- `pip-audit-report.json`

#### 5. Build Docker Image

```yaml
Features:
  - Multi-platform support
  - Build cache (GitHub Actions cache)
  - Push to GHCR
  - Generate SBOM
  
Tags:
  - Branch name (e.g., main, develop)
  - Commit SHA (short)
  - Semver (for tags)
  - latest (for main branch)
```

**Example tags:**
```
ghcr.io/riskcast/riskcast-api:main
ghcr.io/riskcast/riskcast-api:main-a1b2c3d
ghcr.io/riskcast/riskcast-api:v1.2.3
ghcr.io/riskcast/riskcast-api:latest
```

#### 6. Image Scan

```yaml
Tool: Trivy
  - Scans for vulnerabilities
  - Reports CRITICAL and HIGH
  - Uploads to GitHub Security
```

---

## 🚀 CD Pipeline

### Workflow: `.github/workflows/cd.yml`

Runs on:
- Push to `main` → Deploy to Staging
- Push tag `v*` → Deploy to Production
- Manual dispatch → Choose environment

### Jobs

#### 1. Prepare Deployment

Determines:
- Target environment (staging/production)
- Image tag to deploy
- Kubernetes namespace

#### 2. Deploy to Staging

```yaml
Environment: staging
URL: https://staging.api.riskcast.io
Namespace: riskcast-staging

Steps:
  1. Install kubectl & kustomize
  2. Configure kubeconfig
  3. Update image in kustomization
  4. Apply with kustomize
  5. Wait for rollout (5 min timeout)
  6. Run smoke tests
  7. Notify Slack
```

**Manual deployment:**
```bash
# Deploy specific image
gh workflow run cd.yml \
  --field environment=staging \
  --field image_tag=v1.2.3
```

#### 3. Deploy to Production

```yaml
Environment: production
URL: https://api.riskcast.io
Namespace: riskcast-prod

Additional steps:
  - Pre-deployment backup
  - Longer rollout timeout (10 min)
  - Deployment record
  - GitHub deployment
```

**Approval required:** GitHub Environments must be configured with protection rules.

#### 4. Rollback

Automatic rollback on failure:
```bash
kubectl -n riskcast-prod rollout undo deployment/riskcast-api
```

---

## 🔧 ArgoCD Setup

### Installation

```bash
# 1. Create namespace
kubectl create namespace argocd

# 2. Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# 4. Expose ArgoCD (port-forward for testing)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 5. Login
argocd login localhost:8080
argocd account update-password

# 6. Apply applications
kubectl apply -f k8s/argocd/application.yaml
```

### Configuration

Apply custom configuration:
```bash
kubectl apply -f k8s/argocd/install.yaml
kubectl apply -f k8s/argocd/ingress.yaml
```

### Applications

Two applications are created:

#### Production
```yaml
Name: riskcast-api-prod
Source: main branch
Path: k8s/overlays/production
Namespace: riskcast-prod
Sync: Automated with self-heal
```

#### Staging
```yaml
Name: riskcast-api-staging
Source: develop branch
Path: k8s/overlays/staging
Namespace: riskcast-staging
Sync: Automated with self-heal
```

### Access ArgoCD UI

```bash
# Get URL
kubectl get ingress argocd-server-ingress -n argocd

# Or port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser
https://argocd.riskcast.io
# or
https://localhost:8080
```

### ArgoCD CLI Commands

```bash
# List applications
argocd app list

# Get application details
argocd app get riskcast-api-prod

# Sync application
argocd app sync riskcast-api-prod

# View diff
argocd app diff riskcast-api-prod

# Rollback
argocd app rollback riskcast-api-prod

# Delete application
argocd app delete riskcast-api-prod
```

---

## 📦 Release Process

### Workflow: `.github/workflows/release.yml`

### Creating a Release

#### Method 1: Git Tag

```bash
# Create and push tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# This triggers:
# 1. Release workflow
# 2. CI pipeline
# 3. CD pipeline (production)
```

#### Method 2: GitHub UI

1. Go to GitHub → Releases
2. Click "Create a new release"
3. Choose tag (e.g., v1.2.3)
4. Generate release notes
5. Publish release

### Release Workflow

1. **Generate changelog** from commit history
2. **Create GitHub release** with notes
3. **Build assets** (deployment bundle)
4. **Update tags** (latest for stable releases)
5. **Notify Slack**

### Versioning

Follow Semantic Versioning (SemVer):
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (features)
- `v1.0.1` - Patch release (bug fixes)

Pre-releases:
- `v1.0.0-rc.1` - Release candidate
- `v1.0.0-beta.1` - Beta
- `v1.0.0-alpha.1` - Alpha

---

## 🔍 Monitoring Deployments

### GitHub Actions

View workflow runs:
```
https://github.com/<org>/<repo>/actions
```

### ArgoCD Dashboard

View application status:
```
https://argocd.riskcast.io/applications
```

### Kubernetes

```bash
# Check deployment status
kubectl -n riskcast-prod get deployments
kubectl -n riskcast-prod rollout status deployment/riskcast-api

# View pods
kubectl -n riskcast-prod get pods -l app=riskcast-api

# View logs
kubectl -n riskcast-prod logs -f deployment/riskcast-api

# View events
kubectl -n riskcast-prod get events --sort-by='.lastTimestamp'
```

### Slack Notifications

Notifications sent for:
- ✅ Deployment succeeded
- ❌ Deployment failed
- ⚠️ Application unhealthy
- 📦 New release published

---

## 🐛 Troubleshooting

### CI Pipeline Failures

#### Code Quality Failed

```bash
# Fix linting issues
ruff check . --fix

# Format code
black .
isort .

# Check types
mypy app/
```

#### Tests Failed

```bash
# Run locally
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=html
open htmlcov/index.html

# Debug specific test
pytest tests/unit/test_something.py::test_function -vv --pdb
```

#### Build Failed

```bash
# Test Dockerfile locally
docker build -t riskcast-api:test .

# Check build context
docker build --progress=plain -t riskcast-api:test .
```

### CD Pipeline Failures

#### Deployment Failed

```bash
# Check deployment status
kubectl -n riskcast-prod describe deployment riskcast-api

# Check pod status
kubectl -n riskcast-prod get pods
kubectl -n riskcast-prod describe pod <pod-name>

# Check logs
kubectl -n riskcast-prod logs <pod-name>

# Check events
kubectl -n riskcast-prod get events --sort-by='.lastTimestamp'
```

#### Rollback Deployment

```bash
# Via kubectl
kubectl -n riskcast-prod rollout undo deployment/riskcast-api

# Via ArgoCD
argocd app rollback riskcast-api-prod

# To specific revision
kubectl -n riskcast-prod rollout undo deployment/riskcast-api --to-revision=2
```

#### Smoke Tests Failed

```bash
# Run manually
./scripts/smoke-test.sh https://api.riskcast.io

# Check specific endpoint
curl -v https://api.riskcast.io/health/live

# Check from pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never \
  -- curl http://riskcast-api.riskcast-prod.svc.cluster.local/health/live
```

### ArgoCD Issues

#### Application Out of Sync

```bash
# Sync manually
argocd app sync riskcast-api-prod

# Hard refresh
argocd app sync riskcast-api-prod --force

# Prune resources
argocd app sync riskcast-api-prod --prune
```

#### Application Unhealthy

```bash
# Check application details
argocd app get riskcast-api-prod

# View diff
argocd app diff riskcast-api-prod

# Check Kubernetes resources
kubectl -n riskcast-prod get all
```

#### Sync Failed

```bash
# View logs
argocd app logs riskcast-api-prod

# Check sync status
argocd app get riskcast-api-prod --output json | jq '.status.sync'

# Retry sync
argocd app sync riskcast-api-prod --retry-limit 3
```

---

## 📊 Best Practices

### Branch Strategy

```
main
  ├── develop
  │   ├── feature/add-authentication
  │   ├── feature/improve-performance
  │   └── bugfix/fix-login-issue
  └── release/v1.2.0
```

**Flow:**
1. Feature branches → PR to `develop`
2. `develop` → Automatic deploy to staging
3. `develop` → PR to `main` (with approval)
4. `main` → Automatic deploy to staging
5. Tag `main` → Deploy to production

### Commit Messages

Follow Conventional Commits:
```
feat: add user authentication
fix: resolve login timeout issue
docs: update API documentation
chore: upgrade dependencies
test: add integration tests for quotes API
```

### Pull Requests

- **Required checks:** All CI jobs must pass
- **Required reviews:** At least 1 approval
- **Up-to-date:** Branch must be up-to-date with base

### Secrets Management

Never commit secrets to Git. Use:

1. **GitHub Secrets** for CI/CD
   ```
   KUBE_CONFIG_STAGING
   KUBE_CONFIG_PRODUCTION
   SLACK_WEBHOOK_URL
   CODECOV_TOKEN
   ```

2. **Kubernetes Secrets** for applications
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=database-url="..." \
     --namespace=riskcast-prod
   ```

3. **External Secrets** for production
   (See secrets management documentation)

---

## 📚 Additional Resources

- **GitHub Actions Docs:** https://docs.github.com/actions
- **ArgoCD Docs:** https://argo-cd.readthedocs.io/
- **Kustomize Docs:** https://kustomize.io/
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0
