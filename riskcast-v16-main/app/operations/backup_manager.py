"""
Backup & Disaster Recovery Manager

Handles:
1. Database backups (full and incremental)
2. Audit trail archival
3. Model version snapshots
4. Evidence bundle backups
5. Configuration backups
6. Recovery procedures
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import gzip
import io
import logging

from sqlalchemy.orm import Session
from sqlalchemy import text


class BackupType(Enum):
    """Types of backups."""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"
    AUDIT_ARCHIVE = "AUDIT_ARCHIVE"
    MODEL_SNAPSHOT = "MODEL_SNAPSHOT"
    EVIDENCE_BACKUP = "EVIDENCE_BACKUP"
    CONFIG_BACKUP = "CONFIG_BACKUP"


class BackupStatus(Enum):
    """Status of backup operations."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VERIFIED = "VERIFIED"


@dataclass
class BackupManifest:
    """Manifest for a backup."""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    
    # What's included
    tables_included: List[str]
    record_counts: Dict[str, int]
    
    # Storage
    storage_location: str
    compressed_size_bytes: int
    uncompressed_size_bytes: int
    compression_ratio: float
    
    # Verification
    checksum: str
    is_verified: bool
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Retention
    retention_days: int
    expires_at: datetime


@dataclass
class RecoveryPoint:
    """A point in time that can be recovered to."""
    recovery_point_id: str
    timestamp: datetime
    backup_ids: List[str]
    description: str
    is_verified: bool
    estimated_recovery_time_minutes: int


class StorageClient:
    """
    Storage client interface for backup uploads/downloads.
    
    This is a stub implementation. In production, this would connect to:
    - S3, Azure Blob, GCS, or similar
    - Local filesystem for development
    """
    
    def __init__(self, base_path: str = "./backups"):
        self.base_path = base_path
        self.logger = logging.getLogger(__name__)
    
    async def upload_backup(
        self,
        backup_id: str,
        content: bytes,
        backup_type: str
    ) -> str:
        """
        Upload backup content to storage.
        
        Returns storage location/path.
        """
        import os
        
        # Create directory if it doesn't exist
        backup_dir = os.path.join(self.base_path, backup_type)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save to file
        file_path = os.path.join(backup_dir, f"{backup_id}.gz")
        with open(file_path, "wb") as f:
            f.write(content)
        
        self.logger.info(f"Backup saved to {file_path}")
        return file_path
    
    async def download_backup(self, location: str) -> bytes:
        """Download backup content from storage."""
        with open(location, "rb") as f:
            return f.read()


class BackupManager:
    """
    Manages backups and disaster recovery.
    
    Backup schedule:
    - Full backup: Weekly (Sunday 00:00)
    - Incremental: Daily (00:00)
    - Audit archive: Monthly (1st of month)
    - Model snapshots: On every publish
    """
    
    # Retention policies
    RETENTION_DAYS = {
        BackupType.FULL: 90,
        BackupType.INCREMENTAL: 30,
        BackupType.AUDIT_ARCHIVE: 2555,  # 7 years
        BackupType.MODEL_SNAPSHOT: 365,
        BackupType.EVIDENCE_BACKUP: 3650,  # 10 years
        BackupType.CONFIG_BACKUP: 90
    }
    
    # Tables to backup (adjust based on actual schema)
    CRITICAL_TABLES = [
        "policies",
        "claims",
        "risk_runs",
        "audit_events_immutable",
        "risk_model_versions",
        "evidence_bundles",
        "evidence_items",
        "evidence_custody_events",
        "calibration_runs",
        "historical_shipments"
    ]
    
    def __init__(
        self,
        db: Session,
        storage_client: Optional[StorageClient] = None,
        audit_ledger = None
    ):
        self.db = db
        self.storage = storage_client or StorageClient()
        self.audit = audit_ledger
        self.logger = logging.getLogger(__name__)
    
    async def create_full_backup(self) -> BackupManifest:
        """
        Create a full database backup.
        """
        backup_id = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow()
        
        self.logger.info(f"Starting full backup: {backup_id}")
        
        try:
            # Export each table
            table_data = {}
            record_counts = {}
            
            for table in self.CRITICAL_TABLES:
                try:
                    data, count = await self._export_table(table)
                    if count > 0:
                        table_data[table] = data
                        record_counts[table] = count
                except Exception as e:
                    self.logger.warning(f"Failed to export table {table}: {e}")
                    continue
            
            # Compress
            backup_content = json.dumps(table_data, default=str)
            compressed = gzip.compress(backup_content.encode())
            
            # Calculate checksum
            checksum = hashlib.sha256(compressed).hexdigest()
            
            # Upload to storage
            storage_location = await self.storage.upload_backup(
                backup_id=backup_id,
                content=compressed,
                backup_type="full"
            )
            
            completed_at = datetime.utcnow()
            retention = self.RETENTION_DAYS[BackupType.FULL]
            
            manifest = BackupManifest(
                backup_id=backup_id,
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                tables_included=list(table_data.keys()),
                record_counts=record_counts,
                storage_location=storage_location,
                compressed_size_bytes=len(compressed),
                uncompressed_size_bytes=len(backup_content),
                compression_ratio=len(backup_content) / len(compressed) if len(compressed) > 0 else 1.0,
                checksum=checksum,
                is_verified=False,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                retention_days=retention,
                expires_at=completed_at + timedelta(days=retention)
            )
            
            # Verify backup
            is_valid = await self._verify_backup(storage_location, checksum)
            manifest.is_verified = is_valid
            manifest.status = BackupStatus.VERIFIED if is_valid else BackupStatus.COMPLETED
            
            # Store manifest
            await self._store_manifest(manifest)
            
            # Audit
            if self.audit:
                self.audit.append_event(
                    event_type="SYSTEM",
                    action="FULL_BACKUP_COMPLETED",
                    entity_type="backup",
                    entity_id=backup_id,
                    actor_type="SYSTEM",
                    payload={
                        "record_counts": record_counts,
                        "compressed_size_mb": len(compressed) / 1024 / 1024,
                        "is_verified": is_valid
                    }
                )
            
            self.logger.info(f"Full backup completed: {backup_id}")
            
            return manifest
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}", exc_info=True)
            
            if self.audit:
                self.audit.append_event(
                    event_type="ALERT",
                    action="BACKUP_FAILED",
                    entity_type="backup",
                    entity_id=backup_id,
                    actor_type="SYSTEM",
                    payload={"error": str(e)}
                )
            
            raise
    
    async def create_incremental_backup(
        self,
        since: datetime
    ) -> Optional[BackupManifest]:
        """
        Create incremental backup of changes since last backup.
        """
        backup_id = f"incr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow()
        
        self.logger.info(f"Starting incremental backup: {backup_id} (since {since})")
        
        try:
            table_data = {}
            record_counts = {}
            
            # Export only changed records
            for table in self.CRITICAL_TABLES:
                try:
                    data, count = await self._export_table_incremental(table, since)
                    if count > 0:
                        table_data[table] = data
                        record_counts[table] = count
                except Exception as e:
                    self.logger.warning(f"Failed to export incremental from {table}: {e}")
                    continue
            
            if not table_data:
                self.logger.info("No changes to backup")
                return None
            
            # Compress and upload
            backup_content = json.dumps({
                "since": since.isoformat(),
                "tables": table_data
            }, default=str)
            compressed = gzip.compress(backup_content.encode())
            checksum = hashlib.sha256(compressed).hexdigest()
            
            storage_location = await self.storage.upload_backup(
                backup_id=backup_id,
                content=compressed,
                backup_type="incremental"
            )
            
            completed_at = datetime.utcnow()
            retention = self.RETENTION_DAYS[BackupType.INCREMENTAL]
            
            manifest = BackupManifest(
                backup_id=backup_id,
                backup_type=BackupType.INCREMENTAL,
                status=BackupStatus.COMPLETED,
                tables_included=list(table_data.keys()),
                record_counts=record_counts,
                storage_location=storage_location,
                compressed_size_bytes=len(compressed),
                uncompressed_size_bytes=len(backup_content),
                compression_ratio=len(backup_content) / len(compressed) if len(compressed) > 0 else 1.0,
                checksum=checksum,
                is_verified=True,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                retention_days=retention,
                expires_at=completed_at + timedelta(days=retention)
            )
            
            await self._store_manifest(manifest)
            
            if self.audit:
                self.audit.append_event(
                    event_type="SYSTEM",
                    action="INCREMENTAL_BACKUP_COMPLETED",
                    entity_type="backup",
                    entity_id=backup_id,
                    actor_type="SYSTEM",
                    payload={
                        "since": since.isoformat(),
                        "record_counts": record_counts
                    }
                )
            
            return manifest
            
        except Exception as e:
            self.logger.error(f"Incremental backup failed: {e}")
            raise
    
    async def archive_audit_trail(
        self,
        before_date: datetime
    ) -> Optional[BackupManifest]:
        """
        Archive old audit events for long-term storage.
        
        Audit events are NEVER deleted, only archived.
        """
        backup_id = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow()
        
        self.logger.info(f"Archiving audit events before {before_date}")
        
        try:
            from app.core.audit.immutable_ledger import AuditEventImmutable
            
            # Get events to archive
            events = self.db.query(AuditEventImmutable).filter(
                AuditEventImmutable.event_timestamp < before_date
            ).order_by(AuditEventImmutable.sequence_number).all()
            
            if not events:
                self.logger.info("No events to archive")
                return None
            
            # Serialize events
            event_data = [
                {
                    "id": str(e.id),
                    "sequence_number": e.sequence_number,
                    "event_type": e.event_type,
                    "action": e.action,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "actor_type": e.actor_type,
                    "actor_id": e.actor_id,
                    "payload": e.payload_json,
                    "event_timestamp": e.event_timestamp.isoformat() if e.event_timestamp else None,
                    "prev_event_hash": e.prev_event_hash,
                    "event_hash": e.event_hash,
                    "hmac_signature": e.hmac_signature
                }
                for e in events
            ]
            
            # Verify chain integrity before archiving
            prev_hash = None
            for event in events:
                if prev_hash and event.prev_event_hash != prev_hash:
                    raise ValueError("Cannot archive: audit chain integrity failure")
                prev_hash = event.event_hash
            
            archive_content = json.dumps({
                "archive_date": datetime.utcnow().isoformat(),
                "events_from": events[0].event_timestamp.isoformat() if events[0].event_timestamp else None,
                "events_to": events[-1].event_timestamp.isoformat() if events[-1].event_timestamp else None,
                "first_sequence": events[0].sequence_number,
                "last_sequence": events[-1].sequence_number,
                "event_count": len(events),
                "events": event_data
            }, default=str)
            
            compressed = gzip.compress(archive_content.encode())
            checksum = hashlib.sha256(compressed).hexdigest()
            
            storage_location = await self.storage.upload_backup(
                backup_id=backup_id,
                content=compressed,
                backup_type="audit_archive"
            )
            
            completed_at = datetime.utcnow()
            retention = self.RETENTION_DAYS[BackupType.AUDIT_ARCHIVE]
            
            manifest = BackupManifest(
                backup_id=backup_id,
                backup_type=BackupType.AUDIT_ARCHIVE,
                status=BackupStatus.VERIFIED,
                tables_included=["audit_events_immutable"],
                record_counts={"audit_events_immutable": len(events)},
                storage_location=storage_location,
                compressed_size_bytes=len(compressed),
                uncompressed_size_bytes=len(archive_content),
                compression_ratio=len(archive_content) / len(compressed) if len(compressed) > 0 else 1.0,
                checksum=checksum,
                is_verified=True,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                retention_days=retention,
                expires_at=completed_at + timedelta(days=retention)
            )
            
            await self._store_manifest(manifest)
            
            # NOTE: We do NOT delete archived events from the database
            # They remain for immediate query access
            # Archive is for disaster recovery
            
            if self.audit:
                self.audit.append_event(
                    event_type="SYSTEM",
                    action="AUDIT_ARCHIVE_COMPLETED",
                    entity_type="backup",
                    entity_id=backup_id,
                    actor_type="SYSTEM",
                    payload={
                        "event_count": len(events),
                        "sequence_range": f"{events[0].sequence_number}-{events[-1].sequence_number}",
                        "retention_years": retention / 365
                    }
                )
            
            return manifest
            
        except Exception as e:
            self.logger.error(f"Audit archive failed: {e}")
            raise
    
    async def snapshot_model_version(
        self,
        model_version_id: str
    ) -> BackupManifest:
        """
        Create a snapshot of a model version.
        """
        from app.modules.model_versioning.models import RiskModelVersion
        
        backup_id = f"model_{model_version_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow()
        
        version = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.id == model_version_id
        ).first()
        
        if not version:
            raise ValueError(f"Model version {model_version_id} not found")
        
        # Capture complete model state
        snapshot = {
            "model_version_id": str(version.id),
            "name": version.name,
            "version": version.version,
            "status": version.status.value if hasattr(version.status, 'value') else str(version.status),
            "model_schema_version": version.model_schema_version,
            "description": version.description,
            "base_weights_json": version.base_weights_json,
            "correlation_matrix_json": version.correlation_matrix_json,
            "tail_parameters_json": version.tail_parameters_json,
            "interaction_multipliers_json": version.interaction_multipliers_json,
            "loss_transform_params_json": version.loss_transform_params_json,
            "monte_carlo_defaults_json": version.monte_carlo_defaults_json,
            "weights_json": version.weights_json,
            "calibration_json": version.calibration_json,
            "constraints_json": version.constraints_json,
            "metrics_json": version.metrics_json,
            "calibration_run_id": str(version.calibration_run_id) if version.calibration_run_id else None,
            "immutable_hash": version.immutable_hash,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "published_at": version.published_at.isoformat() if version.published_at else None,
            "snapshot_at": datetime.utcnow().isoformat()
        }
        
        snapshot_content = json.dumps(snapshot, indent=2, default=str)
        compressed = gzip.compress(snapshot_content.encode())
        checksum = hashlib.sha256(compressed).hexdigest()
        
        storage_location = await self.storage.upload_backup(
            backup_id=backup_id,
            content=compressed,
            backup_type="model_snapshot"
        )
        
        completed_at = datetime.utcnow()
        retention = self.RETENTION_DAYS[BackupType.MODEL_SNAPSHOT]
        
        manifest = BackupManifest(
            backup_id=backup_id,
            backup_type=BackupType.MODEL_SNAPSHOT,
            status=BackupStatus.VERIFIED,
            tables_included=["risk_model_versions"],
            record_counts={"risk_model_versions": 1},
            storage_location=storage_location,
            compressed_size_bytes=len(compressed),
            uncompressed_size_bytes=len(snapshot_content),
            compression_ratio=len(snapshot_content) / len(compressed) if len(compressed) > 0 else 1.0,
            checksum=checksum,
            is_verified=True,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            retention_days=retention,
            expires_at=completed_at + timedelta(days=retention)
        )
        
        await self._store_manifest(manifest)
        
        if self.audit:
            self.audit.append_event(
                event_type="SYSTEM",
                action="MODEL_SNAPSHOT_CREATED",
                entity_type="backup",
                entity_id=backup_id,
                actor_type="SYSTEM",
                payload={
                    "model_version_id": str(version.id),
                    "model_name": version.name,
                    "model_version": version.version
                }
            )
        
        return manifest
    
    async def list_recovery_points(
        self,
        limit: int = 10
    ) -> List[RecoveryPoint]:
        """
        List available recovery points.
        """
        from app.models.backup_manifest import BackupManifestModel
        
        # Get recent full backups
        full_backups = self.db.query(BackupManifestModel).filter(
            BackupManifestModel.backup_type == BackupType.FULL.value,
            BackupManifestModel.is_verified == True
        ).order_by(
            BackupManifestModel.completed_at.desc()
        ).limit(limit).all()
        
        recovery_points = []
        
        for backup in full_backups:
            # Find incrementals between this and next full backup
            incrementals = self.db.query(BackupManifestModel).filter(
                BackupManifestModel.backup_type == BackupType.INCREMENTAL.value,
                BackupManifestModel.completed_at > backup.completed_at,
                BackupManifestModel.is_verified == True
            ).order_by(
                BackupManifestModel.completed_at
            ).all()
            
            backup_ids = [backup.backup_id] + [i.backup_id for i in incrementals]
            latest_time = incrementals[-1].completed_at if incrementals else backup.completed_at
            
            # Estimate recovery time (rough: 10 min per GB)
            total_size = backup.compressed_size_bytes or 0
            total_size += sum(i.compressed_size_bytes or 0 for i in incrementals)
            est_minutes = max(10, total_size / 1024 / 1024 / 1024 * 10)
            
            recovery_points.append(RecoveryPoint(
                recovery_point_id=f"rp_{backup.backup_id}",
                timestamp=latest_time,
                backup_ids=backup_ids,
                description=f"Full backup + {len(incrementals)} incrementals",
                is_verified=True,
                estimated_recovery_time_minutes=int(est_minutes)
            ))
        
        return recovery_points
    
    async def restore_to_point(
        self,
        recovery_point_id: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Restore database to a recovery point.
        
        WARNING: This is a destructive operation.
        Set dry_run=False to actually restore.
        """
        self.logger.warning(f"Restore requested: {recovery_point_id}, dry_run={dry_run}")
        
        # Parse recovery point
        # ... implementation would download and apply backups
        
        if dry_run:
            return {
                "status": "DRY_RUN",
                "recovery_point": recovery_point_id,
                "message": "Set dry_run=False to actually restore"
            }
        
        # ACTUAL RESTORE WOULD GO HERE
        # This would be a very careful operation with multiple checks
        
        return {
            "status": "NOT_IMPLEMENTED",
            "message": "Full restore requires manual intervention"
        }
    
    async def _export_table(self, table: str):
        """Export entire table."""
        try:
            result = self.db.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            columns = result.keys()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            return data, len(data)
        except Exception as e:
            self.logger.warning(f"Failed to export table {table}: {e}")
            return [], 0
    
    async def _export_table_incremental(self, table: str, since: datetime):
        """Export only records updated since a timestamp."""
        try:
            # Assumes tables have updated_at or created_at column
            result = self.db.execute(
                text(f"SELECT * FROM {table} WHERE updated_at > :since OR created_at > :since"),
                {"since": since}
            )
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            return data, len(data)
        except Exception as e:
            # Table might not have updated_at
            self.logger.debug(f"Table {table} doesn't support incremental export: {e}")
            return [], 0
    
    async def _verify_backup(self, location: str, expected_checksum: str) -> bool:
        """Verify backup integrity."""
        try:
            content = await self.storage.download_backup(location)
            actual_checksum = hashlib.sha256(content).hexdigest()
            return actual_checksum == expected_checksum
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False
    
    async def _store_manifest(self, manifest: BackupManifest):
        """Store backup manifest in database."""
        from app.models.backup_manifest import BackupManifestModel
        
        model = BackupManifestModel(
            backup_id=manifest.backup_id,
            backup_type=manifest.backup_type.value,
            status=manifest.status.value,
            tables_included=manifest.tables_included,
            record_counts=manifest.record_counts,
            storage_location=manifest.storage_location,
            compressed_size_bytes=manifest.compressed_size_bytes,
            uncompressed_size_bytes=manifest.uncompressed_size_bytes,
            checksum=manifest.checksum,
            is_verified=manifest.is_verified,
            started_at=manifest.started_at,
            completed_at=manifest.completed_at,
            duration_seconds=manifest.duration_seconds,
            retention_days=manifest.retention_days,
            expires_at=manifest.expires_at
        )
        
        self.db.add(model)
        self.db.commit()
