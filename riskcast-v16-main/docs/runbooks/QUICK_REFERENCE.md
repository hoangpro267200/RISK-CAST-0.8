# Disaster Recovery - Quick Reference

## 🚀 Quick Commands

### Backup

```bash
# Run backup
python scripts/dr/backup.py

# Full backup
python scripts/dr/backup.py --type full

# List backups
python scripts/dr/restore.py --list
```

### Restore

```bash
# Interactive restore
python scripts/dr/restore.py

# Restore specific backup
python scripts/dr/restore.py --backup-key database/full/YYYYMMDD_HHMMSS/backup.dump

# Drop and restore
python scripts/dr/restore.py --backup-key <key> --drop-existing --yes
```

### Verify

```bash
# Verify database
python scripts/dr/verify.py

# Smoke test
./scripts/smoke-test.sh https://api.riskcast.io
```

---

## 🚨 Emergency Procedures

### Database Corruption

```bash
# 1. Stop app
kubectl scale deployment riskcast-api --replicas=0

# 2. List backups
python scripts/dr/restore.py --list

# 3. Restore
python scripts/dr/restore.py --backup-key <key> --drop-existing --yes

# 4. Verify
python scripts/dr/verify.py

# 5. Restart app
kubectl scale deployment riskcast-api --replicas=3
```

### Region Failure

```bash
# 1. Switch region
export AWS_REGION=us-west-2

# 2. Update DNS
aws route53 change-resource-record-sets --hosted-zone-id <id> --change-batch file://dr-dns.json

# 3. Restore database
python scripts/dr/restore.py --backup-key <key> --yes

# 4. Deploy to DR cluster
kubectl config use-context dr-cluster
kustomize build k8s/overlays/dr | kubectl apply -f -

# 5. Verify
./scripts/smoke-test.sh https://dr.api.riskcast.io
```

### Data Loss

```bash
# 1. Restore to temp database
python scripts/dr/restore.py --backup-key <key> --target-db riskcast_recovery --yes

# 2. Extract data
psql postgresql://...riskcast_recovery -c "COPY (SELECT * FROM quotes WHERE id IN (...)) TO STDOUT CSV HEADER" > recovered.csv

# 3. Import to production
psql $DATABASE_URL -c "\copy quotes FROM 'recovered.csv' CSV HEADER"

# 4. Cleanup
dropdb riskcast_recovery
```

---

## 📊 Recovery Objectives

| Metric | Target |
|--------|--------|
| **RTO** | 4 hours |
| **RPO** | 1 hour |
| **MTTR** | 2 hours |

---

## 📞 Emergency Contacts

| Role | Contact |
|------|---------|
| On-Call | oncall@riskcast.io |
| Database | dba@riskcast.io |
| Security | security@riskcast.io |
| VP Eng | john@riskcast.io |

---

## ✅ Post-Recovery Checklist

- [ ] Health checks passing
- [ ] Database integrity verified
- [ ] Smoke tests passing
- [ ] Monitoring active
- [ ] No error spikes
- [ ] Performance normal
- [ ] Stakeholders notified
- [ ] Incident documented

---

**Print this for emergencies! 📋**
