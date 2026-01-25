# CI/CD Quick Reference

## 🚀 Common Commands

### Local Testing (Before Push)

```bash
# Run all quality checks
ruff check .
black --check .
isort --check-only .
mypy app/

# Fix formatting
black .
isort .

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=html
```

### Deployments

```bash
# Deploy to staging (manual)
gh workflow run cd.yml --field environment=staging

# Deploy to production (manual)
gh workflow run cd.yml --field environment=production --field image_tag=v1.2.3

# Create release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### ArgoCD

```bash
# List apps
argocd app list

# Sync app
argocd app sync riskcast-api-prod

# View status
argocd app get riskcast-api-prod

# Rollback
argocd app rollback riskcast-api-prod
```

### Kubernetes

```bash
# Check deployment
kubectl -n riskcast-prod get deployments
kubectl -n riskcast-prod rollout status deployment/riskcast-api

# View logs
kubectl -n riskcast-prod logs -f deployment/riskcast-api

# Rollback
kubectl -n riskcast-prod rollout undo deployment/riskcast-api
```

---

## 📊 Pipeline Flow

```
Push/PR → CI Pipeline:
  1. Quality ✓
  2. Unit Tests ✓
  3. Integration Tests ✓
  4. Security Scan ✓
  5. Build Image ✓
  6. Scan Image ✓

main branch → Deploy to Staging
v* tag     → Deploy to Production
```

---

## 🔧 Troubleshooting

### CI Failed

```bash
# Check workflow
https://github.com/<repo>/actions

# Run locally
pytest tests/ -v --tb=short
```

### Deployment Failed

```bash
# Check status
kubectl -n riskcast-prod describe deployment riskcast-api

# View logs
kubectl -n riskcast-prod logs -f deployment/riskcast-api

# Rollback
kubectl -n riskcast-prod rollout undo deployment/riskcast-api
```

### ArgoCD Issues

```bash
# Sync manually
argocd app sync riskcast-api-prod --force

# View diff
argocd app diff riskcast-api-prod

# Check health
argocd app get riskcast-api-prod
```

---

## 📋 Checklist

### Before Merging

- [ ] All tests pass
- [ ] Code formatted (black, isort)
- [ ] No linting errors (ruff)
- [ ] Type checking passes (mypy)
- [ ] Security scan clean
- [ ] PR approved
- [ ] Branch up-to-date

### Before Release

- [ ] All features tested in staging
- [ ] Database migrations ready
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Tag created

### After Deployment

- [ ] Smoke tests passed
- [ ] Application healthy
- [ ] No error spikes
- [ ] Metrics normal
- [ ] Team notified

---

## 🔒 Secrets

### GitHub Secrets

```
KUBE_CONFIG_STAGING       - Kubeconfig for staging
KUBE_CONFIG_PRODUCTION    - Kubeconfig for production
SLACK_WEBHOOK_URL         - Slack notifications
CODECOV_TOKEN             - Coverage uploads
```

### Kubernetes Secrets

```bash
# View secrets
kubectl -n riskcast-prod get secrets

# Describe secret
kubectl -n riskcast-prod describe secret riskcast-database-credentials
```

---

## 📚 Quick Links

- **CI Pipeline:** `.github/workflows/ci.yml`
- **CD Pipeline:** `.github/workflows/cd.yml`
- **Release:** `.github/workflows/release.yml`
- **ArgoCD Apps:** `k8s/argocd/application.yaml`
- **Smoke Tests:** `scripts/smoke-test.sh`

---

**Print this for quick reference! 📋**
