# I12: Data Management & Backup Strategy

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft
**Phase:** Continuous (All Phases)
**Dependencies:** I02 (foundation infrastructure)
**Enables:** Data integrity, disaster recovery, reproducibility

---

## Executive Summary

This document specifies the data management and backup strategy for ICCM, consisting of:
- PostgreSQL backup and recovery procedures
- Model checkpoint versioning and archival
- Dataset snapshots and reproducibility
- Disaster recovery planning

**Timeline:** Continuous (implemented in Week 1, maintained throughout)
**Critical Milestone:** Zero data loss, <1 hour recovery time objective (RTO)
**Success Criteria:** All data backed up, recovery procedures tested, reproducibility ensured

---

## Data Classification

### Data Types & Retention

**Tier 1: Critical Data (Permanent Retention)**
- Model checkpoints (all phases)
- Training datasets (40 train + 10 hold-out apps)
- Validation results
- Conversation capture data (I05)

**Tier 2: Important Data (1 Year Retention)**
- Training logs and metrics
- Reconstruction results
- Canary set performance history
- Model routing decisions

**Tier 3: Transient Data (30 Days Retention)**
- Temporary execution results
- Debug logs
- Performance profiling data

### Storage Allocation

**NVMe (4TB - Hot Storage):**
- 1TB: Model weights and checkpoints
- 1TB: PostgreSQL database
- 1TB: Docker volumes and execution
- 1TB: Conversation logs

**HDD (8TB - Cold Storage/Backup):**
- 2TB: Daily PostgreSQL backups (30 days retention)
- 2TB: Model checkpoint archives
- 2TB: Dataset snapshots
- 2TB: Conversation archives (>90 days old)

---

## PostgreSQL Backup Strategy

### Continuous WAL Archiving

**Write-Ahead Log (WAL) Archiving:**

```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /mnt/hdd/postgresql/wal_archive/%f'
archive_timeout = 300  # Archive every 5 minutes
```

**Benefits:**
- Point-in-time recovery (PITR)
- Minimal data loss (<5 minutes)
- Continuous backup without downtime

### Daily Full Backups

**Automated Backup Script:**

```bash
#!/bin/bash
# /mnt/projects/ICCM/scripts/backup_postgres.sh

# Configuration
BACKUP_DIR="/mnt/hdd/postgresql/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Full database backup
pg_basebackup \
    -D $BACKUP_DIR/$DATE \
    -Ft \
    -z \
    -P \
    -U postgres \
    --wal-method=stream

# Verify backup
if [ $? -eq 0 ]; then
    echo "✓ Backup successful: $BACKUP_DIR/$DATE"

    # Create backup manifest
    echo "timestamp: $(date)" > $BACKUP_DIR/$DATE/manifest.txt
    echo "size: $(du -sh $BACKUP_DIR/$DATE | cut -f1)" >> $BACKUP_DIR/$DATE/manifest.txt
    echo "wal_included: yes" >> $BACKUP_DIR/$DATE/manifest.txt

    # Cleanup old backups (>30 days)
    find $BACKUP_DIR -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;
else
    echo "✗ Backup failed"
    exit 1
fi
```

**Cron Schedule:**

```bash
# Daily backups at 2 AM
0 2 * * * /mnt/projects/ICCM/scripts/backup_postgres.sh
```

### Backup Validation

**Weekly Restore Test:**

```bash
#!/bin/bash
# /mnt/projects/ICCM/scripts/test_restore.sh

# Get latest backup
LATEST_BACKUP=$(ls -t /mnt/hdd/postgresql/backups | head -1)

# Create test restore directory
TEST_RESTORE_DIR="/tmp/postgres_restore_test"
mkdir -p $TEST_RESTORE_DIR

# Extract backup
tar -xzf /mnt/hdd/postgresql/backups/$LATEST_BACKUP/base.tar.gz -C $TEST_RESTORE_DIR

# Start temporary PostgreSQL instance
pg_ctl -D $TEST_RESTORE_DIR start

# Validate (run test queries)
psql -d iccm -c "SELECT COUNT(*) FROM conversations;" > /tmp/restore_test_result.txt

# Check result
if grep -q "ERROR" /tmp/restore_test_result.txt; then
    echo "✗ Restore test failed"
    exit 1
else
    echo "✓ Restore test passed"
fi

# Cleanup
pg_ctl -D $TEST_RESTORE_DIR stop
rm -rf $TEST_RESTORE_DIR
```

---

## Model Checkpoint Management

### Versioning Strategy

**Checkpoint Naming Convention:**

```
/mnt/nvme/models/cet-d-{phase}/{checkpoint-type}-{timestamp}

Examples:
- /mnt/nvme/models/cet-d-phase1/checkpoint-20251001_153000
- /mnt/nvme/models/cet-d-phase3/best-20251015_092000
- /mnt/nvme/models/cet-d-phase4/production-20251020_140000
```

**Checkpoint Types:**
- `checkpoint-*`: Regular training checkpoint
- `best-*`: Best validation performance
- `production-*`: Currently deployed in production
- `rollback-*`: Previous production (for rollback)

### Checkpoint Archival

**Archive Strategy:**

```python
#!/usr/bin/env python3
"""
Archive model checkpoints to cold storage.
"""
import shutil
from pathlib import Path
from datetime import datetime, timedelta

CHECKPOINT_DIR = Path("/mnt/nvme/models")
ARCHIVE_DIR = Path("/mnt/hdd/model_archives")
RETENTION_POLICY = {
    'checkpoint': 7,      # Keep regular checkpoints for 7 days
    'best': 90,           # Keep best checkpoints for 90 days
    'production': None,   # Keep all production checkpoints forever
    'rollback': 30        # Keep rollback checkpoints for 30 days
}

def archive_checkpoints():
    """
    Archive old checkpoints based on retention policy.
    """
    for phase_dir in CHECKPOINT_DIR.glob("cet-d-*"):
        for checkpoint in phase_dir.glob("*-*"):
            # Parse checkpoint type and timestamp
            checkpoint_type = checkpoint.name.split('-')[0]
            timestamp_str = checkpoint.name.split('-', 1)[1]
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

            # Check retention
            retention_days = RETENTION_POLICY.get(checkpoint_type)

            if retention_days is None:
                # Keep forever (production checkpoints)
                continue

            age_days = (datetime.now() - timestamp).days

            if age_days > retention_days:
                # Archive to HDD
                archive_path = ARCHIVE_DIR / phase_dir.name / checkpoint.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)

                print(f"Archiving {checkpoint} → {archive_path}")
                shutil.move(str(checkpoint), str(archive_path))

                # Compress
                shutil.make_archive(str(archive_path), 'gztar', str(archive_path))
                shutil.rmtree(archive_path)  # Remove uncompressed

if __name__ == "__main__":
    archive_checkpoints()
```

**Cron Schedule:**

```bash
# Weekly checkpoint archival (Sundays at 3 AM)
0 3 * * 0 python /mnt/projects/ICCM/scripts/archive_checkpoints.py
```

---

## Dataset Snapshots

### Training Dataset Versioning

**Snapshot Creation:**

```bash
#!/bin/bash
# /mnt/projects/ICCM/scripts/snapshot_dataset.sh

DATASET_DIR="/mnt/projects/ICCM/datasets/applications"
SNAPSHOT_DIR="/mnt/hdd/dataset_snapshots"
DATE=$(date +%Y%m%d)
VERSION="v3.0"  # Update when dataset changes

# Create snapshot
SNAPSHOT_NAME="iccm_dataset_${VERSION}_${DATE}"
SNAPSHOT_PATH="$SNAPSHOT_DIR/$SNAPSHOT_NAME"

mkdir -p $SNAPSHOT_PATH

# Copy dataset
rsync -av --progress $DATASET_DIR/ $SNAPSHOT_PATH/

# Create manifest
cat > $SNAPSHOT_PATH/manifest.json <<EOF
{
  "version": "$VERSION",
  "snapshot_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_apps": $(find $SNAPSHOT_PATH -name "metadata.json" | wc -l),
  "train_apps": $(find $SNAPSHOT_PATH/train -name "metadata.json" | wc -l),
  "holdout_apps": $(find $SNAPSHOT_PATH/holdout -name "metadata.json" | wc -l),
  "total_size_bytes": $(du -sb $SNAPSHOT_PATH | cut -f1)
}
EOF

# Compress
tar -czf $SNAPSHOT_DIR/$SNAPSHOT_NAME.tar.gz -C $SNAPSHOT_DIR $SNAPSHOT_NAME
rm -rf $SNAPSHOT_PATH  # Remove uncompressed

# Compute checksum
sha256sum $SNAPSHOT_DIR/$SNAPSHOT_NAME.tar.gz > $SNAPSHOT_DIR/$SNAPSHOT_NAME.tar.gz.sha256

echo "✓ Dataset snapshot created: $SNAPSHOT_NAME.tar.gz"
```

**Snapshot Triggers:**
- Before starting Phase 1 training (baseline)
- After dataset expansion (10 → 50 apps)
- Before any major dataset modifications

---

## Conversation Archive

### Long-Term Storage Strategy

**Archive Old Conversations (>90 days):**

```python
#!/usr/bin/env python3
"""
Archive old conversations to cold storage.
"""
import psycopg
import json
from pathlib import Path
from datetime import datetime, timedelta

ARCHIVE_DIR = Path("/mnt/hdd/conversation_archives")
ARCHIVE_THRESHOLD_DAYS = 90

def archive_old_conversations():
    """
    Move conversations older than 90 days to cold storage.
    """
    with psycopg.connect("postgresql://iccm:password@localhost:5432/iccm") as conn:
        # Get old conversations
        cutoff_date = datetime.now() - timedelta(days=ARCHIVE_THRESHOLD_DAYS)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, session_id, timestamp, speaker, content, metadata
                FROM conversations
                WHERE timestamp < %s
                AND archived = FALSE
                ORDER BY timestamp
                """,
                (cutoff_date,)
            )

            old_conversations = cur.fetchall()

        if not old_conversations:
            print("No conversations to archive")
            return

        # Group by month
        monthly_archives = {}
        for conv in old_conversations:
            month_key = conv[2].strftime("%Y-%m")  # timestamp
            if month_key not in monthly_archives:
                monthly_archives[month_key] = []
            monthly_archives[month_key].append({
                'id': conv[0],
                'session_id': str(conv[1]),
                'timestamp': conv[2].isoformat(),
                'speaker': conv[3],
                'content': conv[4],
                'metadata': conv[5]
            })

        # Write monthly archive files
        for month, conversations in monthly_archives.items():
            archive_file = ARCHIVE_DIR / f"conversations_{month}.jsonl.gz"
            archive_file.parent.mkdir(parents=True, exist_ok=True)

            import gzip
            with gzip.open(archive_file, 'at') as f:
                for conv in conversations:
                    f.write(json.dumps(conv) + '\n')

            # Mark as archived in database
            conv_ids = [conv['id'] for conv in conversations]
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE conversations
                    SET archived = TRUE, archive_file = %s
                    WHERE id = ANY(%s)
                    """,
                    (str(archive_file), conv_ids)
                )
                conn.commit()

            print(f"✓ Archived {len(conversations)} conversations to {archive_file}")

if __name__ == "__main__":
    archive_old_conversations()
```

**Monthly Archival Schedule:**

```bash
# First day of each month at 4 AM
0 4 1 * * python /mnt/projects/ICCM/scripts/archive_conversations.py
```

---

## Disaster Recovery Plan

### Recovery Time Objective (RTO): 1 Hour

**Scenario 1: Database Corruption**

```bash
#!/bin/bash
# /mnt/projects/ICCM/scripts/recover_database.sh

# 1. Stop PostgreSQL
systemctl stop postgresql

# 2. Identify latest valid backup
LATEST_BACKUP=$(ls -t /mnt/hdd/postgresql/backups | head -1)

# 3. Restore from backup
rm -rf /var/lib/postgresql/15/main/*
tar -xzf /mnt/hdd/postgresql/backups/$LATEST_BACKUP/base.tar.gz -C /var/lib/postgresql/15/main/

# 4. Restore WAL archives (point-in-time recovery)
cp /mnt/hdd/postgresql/wal_archive/* /var/lib/postgresql/15/main/pg_wal/

# 5. Configure recovery
cat > /var/lib/postgresql/15/main/recovery.conf <<EOF
restore_command = 'cp /mnt/hdd/postgresql/wal_archive/%f %p'
recovery_target_time = 'latest'
EOF

# 6. Start PostgreSQL (recovery mode)
systemctl start postgresql

# 7. Verify
psql -d iccm -c "SELECT COUNT(*) FROM conversations;"

echo "✓ Database recovery complete"
```

**Scenario 2: Model Checkpoint Loss**

```bash
#!/bin/bash
# /mnt/projects/ICCM/scripts/recover_checkpoint.sh

MODEL_NAME=$1  # e.g., "cet-d-phase3-best"

# 1. Find checkpoint in archives
ARCHIVE_PATH=$(find /mnt/hdd/model_archives -name "$MODEL_NAME*.tar.gz" | head -1)

if [ -z "$ARCHIVE_PATH" ]; then
    echo "✗ Checkpoint not found in archives"
    exit 1
fi

# 2. Extract to NVMe
RESTORE_PATH="/mnt/nvme/models/$(basename $ARCHIVE_PATH .tar.gz)"
tar -xzf $ARCHIVE_PATH -C /mnt/nvme/models/

# 3. Verify integrity
python -c "
from transformers import AutoModel
model = AutoModel.from_pretrained('$RESTORE_PATH')
print('✓ Model loaded successfully')
"

echo "✓ Checkpoint recovered: $RESTORE_PATH"
```

**Scenario 3: Complete Hardware Failure**

**Recovery Procedure:**
1. Provision replacement hardware (same specs)
2. Install OS and dependencies
3. Restore PostgreSQL from HDD backup
4. Restore model checkpoints from HDD archives
5. Restore dataset from snapshot
6. Resume from latest checkpoint

**Expected RTO:** 4-8 hours (hardware procurement is bottleneck)

---

## Reproducibility Package

### Research Reproducibility

**Package Contents:**

```
/mnt/hdd/reproducibility_package/
├── README.md                    # Setup instructions
├── hardware_specs.txt           # Exact hardware configuration
├── software_versions.txt        # All dependency versions
├── dataset/
│   └── iccm_dataset_v3.0.tar.gz
├── models/
│   ├── cet-d-phase1-final.tar.gz
│   ├── cet-d-phase2-final.tar.gz
│   ├── cet-d-phase3-final.tar.gz
│   └── cet-d-phase4-final.tar.gz
├── code/
│   └── iccm_training_code_v1.0.tar.gz
├── results/
│   ├── training_logs/
│   ├── validation_results.json
│   └── statistical_tests.json
└── checksums.sha256
```

**Package Creation Script:**

```bash
#!/bin/bash
# /mnt/projects/ICCM/scripts/create_reproducibility_package.sh

PACKAGE_DIR="/mnt/hdd/reproducibility_package"
mkdir -p $PACKAGE_DIR/{dataset,models,code,results/training_logs}

# 1. Hardware specs
lshw > $PACKAGE_DIR/hardware_specs.txt

# 2. Software versions
pip freeze > $PACKAGE_DIR/software_versions.txt
nvidia-smi --query-gpu=driver_version --format=csv,noheader > $PACKAGE_DIR/gpu_driver_version.txt

# 3. Dataset
cp /mnt/hdd/dataset_snapshots/iccm_dataset_v3.0_*.tar.gz $PACKAGE_DIR/dataset/

# 4. Models
for model in /mnt/nvme/models/cet-d-*final; do
    tar -czf $PACKAGE_DIR/models/$(basename $model).tar.gz $model
done

# 5. Code
git archive --format=tar.gz --output=$PACKAGE_DIR/code/iccm_training_code_v1.0.tar.gz HEAD

# 6. Results
cp -r /mnt/projects/ICCM/validation/results/* $PACKAGE_DIR/results/
cp /mnt/projects/ICCM/training/*/training.log $PACKAGE_DIR/results/training_logs/

# 7. Checksums
cd $PACKAGE_DIR
find . -type f -exec sha256sum {} \; > checksums.sha256

# 8. Create final archive
cd ..
tar -czf iccm_reproducibility_package_v1.0.tar.gz reproducibility_package/

echo "✓ Reproducibility package created: iccm_reproducibility_package_v1.0.tar.gz"
```

---

## Monitoring & Alerting

### Backup Health Monitoring

**Prometheus Metrics:**

```python
from prometheus_client import Gauge, Counter

backup_last_success_timestamp = Gauge('backup_last_success_timestamp', 'Last successful backup')
backup_size_bytes = Gauge('backup_size_bytes', 'Backup size', ['type'])
backup_duration_seconds = Gauge('backup_duration_seconds', 'Backup duration', ['type'])
backup_failures_total = Counter('backup_failures_total', 'Total backup failures', ['type'])
```

**Alert Rules:**

```yaml
groups:
  - name: backup_alerts
    rules:
      - alert: BackupFailed
        expr: time() - backup_last_success_timestamp > 86400
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Backup has not succeeded in 24 hours"

      - alert: BackupSizeAnomalous
        expr: abs(backup_size_bytes - avg_over_time(backup_size_bytes[7d])) > 0.5 * avg_over_time(backup_size_bytes[7d])
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Backup size is anomalous (>50% deviation from 7-day average)"
```

---

## Validation & Testing

### Backup Validation

**Weekly Tests:**
- Restore PostgreSQL from latest backup
- Verify data integrity (row counts, checksums)
- Load model checkpoint and validate

**Monthly Tests:**
- Full disaster recovery simulation
- Restore from archives (not just latest backup)
- Measure actual RTO

### Checklist

**Weekly Backup Validation:**
- [ ] PostgreSQL backup completed successfully
- [ ] WAL archiving operational
- [ ] Model checkpoints archived
- [ ] Conversation data backed up
- [ ] Restore test passed
- [ ] All checksums valid

**Monthly Disaster Recovery Test:**
- [ ] Full database restore successful
- [ ] Model checkpoints recoverable from archives
- [ ] Dataset snapshot restored
- [ ] System operational within 1 hour RTO
- [ ] All data integrity checks passed

---

## Deliverables

### Week 1 Deliverables (Initial Setup):
- [x] PostgreSQL WAL archiving configured
- [x] Daily backup cron jobs scheduled
- [x] Checkpoint archival script implemented
- [x] Dataset snapshot created

### Continuous Deliverables:
- [x] Daily PostgreSQL backups (30 days retention)
- [x] Weekly restore tests
- [x] Monthly disaster recovery tests
- [x] Reproducibility package updated after major milestones

**Exit Criteria:** All backup procedures validated, disaster recovery tested, zero data loss demonstrated

---

## References

- **Paper 08:** Test Lab Infrastructure (storage specifications)
- **Paper 11:** Testing Infrastructure (data requirements)
- **Paper 12:** Conversation Storage & Retrieval (conversation data)
- **I02:** Foundation Layer (PostgreSQL setup)
- **I05:** Conversation Capture (conversation data source)
- **I08:** Phase 3 Training (model checkpoints)
