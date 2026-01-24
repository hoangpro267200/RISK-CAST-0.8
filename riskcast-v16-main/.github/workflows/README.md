# GitHub Actions Workflows

This directory contains CI/CD workflows for RISKCAST V3.

## Workflows

### `ci.yml` - Continuous Integration

Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**
1. **Lint & Type Check**: Runs Ruff linter and optional mypy type checking
2. **Unit Tests**: Runs unit tests with coverage reporting
3. **Integration Tests**: Runs integration tests against MySQL and Redis services
4. **Security Scan**: Runs Bandit and Safety security scans
5. **Build Docker Image**: Builds and pushes Docker image to GitHub Container Registry

**Features:**
- Caching for faster builds
- Code coverage reporting to Codecov
- Test result artifacts
- Security scan reports

### `deploy.yml` - Continuous Deployment

Runs on pushes to `main` and manual workflow dispatch.

**Environments:**
1. **Staging**: Auto-deploys on push to `main`
2. **Production**: Manual deployment with approval

**Steps:**
- Updates Kubernetes deployments
- Runs database migrations (production only)
- Performs smoke tests
- Sends Slack notifications

### `dependabot.yml` - Dependabot Auto-merge

Automatically merges Dependabot PRs for patch and minor version updates.

## Required Secrets

### CI Secrets

- `CODECOV_TOKEN`: Codecov token for coverage reporting (optional)

### Deployment Secrets

- `AWS_ACCESS_KEY_ID`: AWS access key for EKS access
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)
- `EKS_CLUSTER_NAME_STAGING`: EKS cluster name for staging
- `EKS_CLUSTER_NAME_PRODUCTION`: EKS cluster name for production
- `STAGING_API_URL`: Staging API URL for smoke tests
- `PRODUCTION_API_URL`: Production API URL for verification
- `SLACK_BOT_TOKEN`: Slack bot token for notifications (optional)
- `SLACK_CHANNEL_ID`: Slack channel ID for notifications (optional)

## Environment Setup

### GitHub Environments

Create environments in GitHub repository settings:

1. **staging**
   - No protection rules (auto-deploy)
   - URL: https://staging-api.riskcast.com

2. **production**
   - Required reviewers: Add team members
   - Deployment branches: Only `main`
   - URL: https://api.riskcast.com

## Usage

### Manual Deployment

1. Go to Actions tab
2. Select "Deploy" workflow
3. Click "Run workflow"
4. Select environment (staging/production)
5. Click "Run workflow"

### Viewing Results

- **CI Results**: Actions tab → CI workflow
- **Coverage**: Codecov dashboard (if configured)
- **Security Reports**: Download artifacts from CI workflow
- **Deployment Status**: Environments tab in repository settings

## Troubleshooting

### Build Failures

- Check logs in Actions tab
- Verify secrets are configured
- Check Docker image build logs

### Deployment Failures

- Verify AWS credentials
- Check EKS cluster access
- Verify namespace exists in cluster
- Check kubectl commands in logs

### Test Failures

- Check test logs in Actions artifacts
- Verify MySQL/Redis services are running
- Check database connection strings

## Customization

### Adding New Jobs

Add new jobs to `ci.yml`:

```yaml
new-job:
  name: New Job
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    # ... your steps
```

### Changing Test Commands

Modify test commands in `test-unit` and `test-integration` jobs.

### Adding Environments

Add new environments to `deploy.yml`:

```yaml
deploy-new-env:
  name: Deploy to New Environment
  runs-on: ubuntu-latest
  environment:
    name: new-env
  steps:
    # ... deployment steps
```
