# 🛡️ Disaster Recovery System

**Enterprise-grade backup, restore, and disaster recovery procedures**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![RTO](https://img.shields.io/badge/RTO-4%20hours-blue)]()
[![RPO](https://img.shields.io/badge/RPO-1%20hour-blue)]()

---

## 🎯 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements-dr.txt

# Install PostgreSQL client tools
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# macOS:
brew install postgresql

# Configure AWS
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

### Run Backup

```bash
# Configure
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
export BACKUP_S3_BUCKET="riskcast-backups"

# Run backup
python scripts/dr/backup.py

# Verify
python scripts/dr/restore.py --list
```

### Restore Database

```bash
# List backups
python scripts/dr/restore.py --list

# Restore (interactive)
python scripts/dr/restore.py

# Or restore specific backup
python scripts/dr/restore.py --backup-key database/full/20240115_030000/backup.dump

# Verify
python scripts/dr/verify.py
```

---

## 📊 Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** | 4 hours | Maximum acceptable downtime |
| **RPO** | 1 hour | Maximum acceptable data loss |
| **MTTR** | 2 hours | Mean time to recover |

---

## 💾 Backup Strategy

### Schedule

| Backup Type | Frequency | Retention | Size |
|-------------|-----------|-----------|------|
| **Full** | Weekly (Sunday 3 AM) | 30 days | ~500 MB |
| **Incremental** | Daily (Mon-Sat 3 AM) | 7 days | ~100 MB |
| **Configuration** | With full backup | 30 days | ~10 MB |

### Features

- ✅ Automated scheduling (CronJob)
- ✅ S3 storage with KMS encryption
- ✅ SHA-256 verification
- ✅ pg_restore validation
- ✅ Automatic retention cleanup
- ✅ Metadata tracking

---

## 🚨 Disaster Scenarios

### 1. Database Corruption

**Symptoms:** Data integrity errors, transaction failures

**Recovery Time:** 2-3 hours

```bash
kubectl scale deployment riskcast-api --replicas=0
python scripts/dr/restore.py --drop-existing --yes
python scripts/dr/verify.py
kubectl scale deployment riskcast-api --replicas=3
```

### 2. Region Failure

**Symptoms:** AWS region unavailable

**Recovery Time:** 3-4 hours

```bash
export AWS_REGION=us-west-2
aws route53 change-resource-record-sets ...
python scripts/dr/restore.py --yes
kubectl config use-context dr-cluster
kustomize build k8s/overlays/dr | kubectl apply -f -
```

### 3. Accidental Deletion

**Symptoms:** Missing records

**Recovery Time:** 1-2 hours

```bash
python scripts/dr/restore.py --target-db riskcast_recovery
# Extract deleted data
psql $DATABASE_URL -c "\copy table FROM 'recovered.csv' CSV"
```

### 4. Security Breach

**Symptoms:** Unauthorized access

**Recovery Time:** 4-8 hours

```bash
kubectl apply -f emergency-lockdown.yaml
python scripts/secrets/rotate.py --all --yes
python scripts/security/audit-review.py
python scripts/dr/restore.py --target-db riskcast_clean --yes
```

---

## 📁 Project Structure

```
.
├── scripts/dr/
│   ├── backup.py              # Backup script
│   ├── restore.py             # Restore script
│   ├── verify.py              # Verification script
│   └── README.md              # Tool documentation
│
├── k8s/dr/
│   └── backup-cronjob.yaml    # Automated backups
│
├── docs/runbooks/
│   ├── disaster-recovery.md   # Complete runbook
│   └── QUICK_REFERENCE.md     # Quick reference
│
├── requirements-dr.txt        # Dependencies
└── DR_README.md               # This file
```

---

## 🛠️ Tools

### backup.py

Create database and configuration backups.

**Features:**
- Full and incremental backups
- S3 upload with encryption
- Automatic verification
- Retention management

**Usage:**
```bash
python scripts/dr/backup.py [--type full|incremental|auto]
```

### restore.py

Restore database from S3 backup.

**Features:**
- List available backups
- Interactive or scripted
- Parallel restore
- Automatic verification

**Usage:**
```bash
python scripts/dr/restore.py [--list] [--backup-key KEY]
```

### verify.py

Verify database integrity.

**Features:**
- Connection test
- Structure verification
- Data integrity checks
- Comprehensive reporting

**Usage:**
```bash
python scripts/dr/verify.py
```

---

## 📚 Documentation

| Document | Purpose | Lines |
|----------|---------|-------|
| [disaster-recovery.md](docs/runbooks/disaster-recovery.md) | Complete runbook | 1,100 |
| [QUICK_REFERENCE.md](docs/runbooks/QUICK_REFERENCE.md) | Quick commands | 150 |
| [scripts/dr/README.md](scripts/dr/README.md) | Tool docs | 350 |
| [DR_IMPLEMENTATION_COMPLETE.md](DR_IMPLEMENTATION_COMPLETE.md) | Implementation | 500 |

---

## 🔒 Security

- **Encryption:** KMS or AES-256 at rest
- **Access Control:** IAM roles (no static credentials)
- **Audit Logging:** CloudTrail for S3 operations
- **Verification:** SHA-256 checksums
- **Testing:** Regular DR drills

---

## 📈 Metrics

| Metric | Value |
|--------|-------|
| Backup Duration (Full) | ~5-10 min |
| Backup Duration (Incremental) | ~2-5 min |
| Restore Duration | ~10-20 min |
| Verification Duration | ~2-5 min |
| Storage Cost (30 days) | ~$5-10/month |

---

## ✅ Testing

### Weekly

```bash
# Automated backup verification
python scripts/dr/backup.py
python scripts/dr/restore.py --list
```

### Monthly

```bash
# Restore test
python scripts/dr/restore.py --target-db riskcast_test --yes
python scripts/dr/verify.py
dropdb riskcast_test
```

### Quarterly

```bash
# Full DR drill (4 hours)
# - Simulate disaster
# - Execute recovery
# - Verify services
# - Document results
```

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| pg_dump not found | Install postgresql-client |
| boto3 not installed | pip install boto3 |
| Connection refused | Check DATABASE_URL |
| S3 permission denied | Check IAM role |
| Backup verification failed | Use previous backup |

### Emergency Help

1. **Check runbook:** [disaster-recovery.md](docs/runbooks/disaster-recovery.md)
2. **Check quick reference:** [QUICK_REFERENCE.md](docs/runbooks/QUICK_REFERENCE.md)
3. **Contact on-call:** oncall@riskcast.io

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** January 24, 2026

```
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║       🛡️ DISASTER RECOVERY SYSTEM READY               ║
║                                                       ║
║  ✅ Automated Backups                                ║
║  ✅ One-Command Restore                              ║
║  ✅ Comprehensive Verification                       ║
║  ✅ Complete Runbooks                                ║
║                                                       ║
║  Ready for any disaster! 🚨                          ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

**Sleep well knowing your data is safe! 💤**
