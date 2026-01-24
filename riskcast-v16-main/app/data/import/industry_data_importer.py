"""
Industry Data Importer

Imports historical shipment/loss data from external sources:
- Insurance industry databases (Lloyd's, etc.)
- Shipping company data feeds
- Claims databases
- Partner data shares

This is how we build the calibration dataset.
"""

import csv
import json
import httpx
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Generator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib
import logging

from sqlalchemy.orm import Session

from app.data.historical.loss_data_repository import (
    HistoricalLossDataRepository,
    ShipmentOutcome,
    ClaimStatus
)
from app.core.data_quality.validation import DataValidator, get_data_validator

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """External data sources."""
    LLOYDS_LIST = "LLOYDS_LIST"
    TT_CLUB = "TT_CLUB"
    CEFOR = "CEFOR"
    IUMI = "IUMI"
    PARTNER_SHIPPER = "PARTNER_SHIPPER"
    PARTNER_CARRIER = "PARTNER_CARRIER"
    PARTNER_INSURER = "PARTNER_INSURER"
    INTERNAL_CLAIMS = "INTERNAL_CLAIMS"
    INTERNAL_POLICIES = "INTERNAL_POLICIES"


@dataclass
class ImportConfig:
    """Configuration for data import."""
    source: DataSource
    file_path: Optional[Path] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    
    # Field mappings (source field -> our field)
    field_mappings: Dict[str, str] = None
    
    # Value mappings (source value -> our value)
    outcome_mappings: Dict[str, ShipmentOutcome] = None
    claim_status_mappings: Dict[str, ClaimStatus] = None
    
    # Data quality settings
    min_completeness: float = 0.5
    require_loss_data: bool = False
    
    # Date parsing
    date_format: str = "%Y-%m-%d"
    
    def __post_init__(self):
        if self.field_mappings is None:
            self.field_mappings = {}
        if self.outcome_mappings is None:
            self.outcome_mappings = {}
        if self.claim_status_mappings is None:
            self.claim_status_mappings = {}


@dataclass
class ImportResult:
    """Result of data import."""
    source: DataSource
    total_records: int
    imported_records: int
    skipped_records: int
    error_records: int
    errors: List[Dict[str, Any]]
    import_hash: str
    started_at: datetime
    completed_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source.value,
            "total_records": self.total_records,
            "imported_records": self.imported_records,
            "skipped_records": self.skipped_records,
            "error_records": self.error_records,
            "errors": self.errors,
            "import_hash": self.import_hash,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "success_rate": self.imported_records / self.total_records if self.total_records > 0 else 0,
        }


class IndustryDataImporter:
    """
    Imports historical data from various industry sources.
    
    This is the primary way to build calibration datasets.
    """
    
    def __init__(
        self,
        db: Session,
        audit: Optional[Any],
        repository: HistoricalLossDataRepository
    ):
        self.db = db
        self.audit = audit
        self.repository = repository
        self.logger = logging.getLogger(__name__)
        self.client = httpx.AsyncClient(timeout=60.0)
        self.validator = get_data_validator(audit)
    
    async def import_from_csv(
        self,
        file_path: Path,
        config: ImportConfig
    ) -> ImportResult:
        """Import historical data from CSV file."""
        started_at = datetime.utcnow()
        
        total = 0
        imported = 0
        skipped = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    total += 1
                    
                    try:
                        # Map fields
                        mapped_data = self._map_fields(row, config)
                        
                        # Validate with DataValidator
                        validation_result = self.validator.validate_shipment_data(
                            mapped_data,
                            context=f"CSV_IMPORT:{file_path.name}"
                        )
                        
                        # Check basic validation
                        is_valid, validation_errors = self._validate_record(mapped_data, config)
                        if not is_valid:
                            skipped += 1
                            if validation_errors:
                                errors.append({
                                    "row": total,
                                    "errors": validation_errors,
                                    "validation_issues": [i.to_dict() for i in validation_result.issues],
                                    "data": {k: v for k, v in row.items() if k in config.field_mappings}
                                })
                            continue
                        
                        # Log validation warnings
                        if validation_result.warnings:
                            self.logger.debug(
                                f"Row {total} validation warnings: "
                                f"{[w.message for w in validation_result.warnings]}"
                            )
                        
                        # Determine outcome
                        outcome = self._determine_outcome(mapped_data, config)
                        
                        # Import
                        await self.repository.ingest_shipment_outcome(
                            shipment_data=mapped_data,
                            outcome=outcome,
                            source=config.source.value,
                            source_reference=f"{file_path.name}:row_{total}"
                        )
                        
                        imported += 1
                        
                    except Exception as e:
                        errors.append({
                            "row": total,
                            "error": str(e),
                            "data": {k: v for k, v in row.items() if k in config.field_mappings}
                        })
                        self.logger.error(f"Error importing row {total}: {e}")
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
            errors.append({"file_error": str(e)})
        
        completed_at = datetime.utcnow()
        
        # Compute import hash
        import_hash = self._compute_import_hash(file_path, config, imported)
        
        result = ImportResult(
            source=config.source,
            total_records=total,
            imported_records=imported,
            skipped_records=skipped,
            error_records=len(errors),
            errors=errors[:100],  # Limit stored errors
            import_hash=import_hash,
            started_at=started_at,
            completed_at=completed_at
        )
        
        # Audit the import
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="DATA_IMPORT",
                    action="HISTORICAL_DATA_IMPORTED",
                    entity_type="import_batch",
                    entity_id=import_hash,
                    actor_type="SYSTEM",
                    payload={
                        "source": config.source.value,
                        "file": str(file_path),
                        "total": total,
                        "imported": imported,
                        "skipped": skipped,
                        "errors": len(errors)
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit import: {e}")
        
        return result
    
    async def import_from_lloyds_list(
        self,
        api_key: str,
        start_date: date,
        end_date: date
    ) -> ImportResult:
        """Import from Lloyd's List Intelligence API."""
        # Lloyd's List field mappings
        config = ImportConfig(
            source=DataSource.LLOYDS_LIST,
            file_path=None,
            api_endpoint="https://api.lloydslistintelligence.com/v1/casualties",
            api_key=api_key,
            field_mappings={
                "vessel_name": "vessel_name",
                "incident_date": "shipment_date",
                "departure_port": "origin_port",
                "destination_port": "destination_port",
                "cargo_description": "cargo_type",
                "cargo_value_usd": "cargo_value_usd",
                "incident_type": "loss_type",
                "loss_amount": "loss_amount_usd",
                "cause": "loss_cause",
                "description": "loss_description"
            },
            outcome_mappings={
                "total_loss": ShipmentOutcome.TOTAL_LOSS,
                "partial_loss": ShipmentOutcome.PARTIAL_LOSS,
                "damage": ShipmentOutcome.DAMAGE_MAJOR,
                "fire": ShipmentOutcome.DAMAGE_MAJOR,
                "collision": ShipmentOutcome.DAMAGE_MAJOR,
                "grounding": ShipmentOutcome.PARTIAL_LOSS,
                "piracy": ShipmentOutcome.THEFT,
                "theft": ShipmentOutcome.THEFT,
            },
            claim_status_mappings={},
            require_loss_data=True  # Lloyd's List only has incidents
        )
        
        # Fetch from API
        records = await self._fetch_from_api(config, {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        })
        
        return await self._import_records(records, config, source_ref="lloyds_list")
    
    async def import_from_partner_shipper(
        self,
        partner_id: str,
        data: List[Dict[str, Any]],
        field_mappings: Dict[str, str]
    ) -> ImportResult:
        """Import data from a partner shipper."""
        config = ImportConfig(
            source=DataSource.PARTNER_SHIPPER,
            file_path=None,
            api_endpoint=None,
            api_key=None,
            field_mappings=field_mappings,
            outcome_mappings={
                "delivered": ShipmentOutcome.DELIVERED_ON_TIME,
                "delivered_late": ShipmentOutcome.DELIVERED_LATE,
                "lost": ShipmentOutcome.TOTAL_LOSS,
                "damaged": ShipmentOutcome.DAMAGE_MINOR,
                "damaged_severe": ShipmentOutcome.DAMAGE_MAJOR,
            },
            claim_status_mappings={
                "no_claim": ClaimStatus.NO_CLAIM,
                "filed": ClaimStatus.CLAIM_FILED,
                "approved": ClaimStatus.CLAIM_APPROVED,
                "denied": ClaimStatus.CLAIM_DENIED,
            }
        )
        
        return await self._import_records(data, config, source_ref=partner_id)
    
    async def import_internal_claims(self) -> ImportResult:
        """Import from internal claims database to historical data."""
        # Try to import from claims models if available
        try:
            from app.modules.claims.models import Claim, ClaimStatus
            from app.modules.underwriting.models import Policy
            
            # Get all closed claims
            claims = self.db.query(Claim).filter(
                Claim.status == ClaimStatus.CLOSED
            ).all()
            
            records = []
            for claim in claims:
                policy = self.db.query(Policy).filter(Policy.id == claim.policy_id).first()
                if not policy:
                    continue
                
                # Build record from claim + policy
                # Policy terms might be in risk_run or submission
                policy_terms = {}
                risk_snapshot = {}
                
                # Try to get terms from risk_run
                if hasattr(policy, 'risk_run') and policy.risk_run:
                    risk_run = policy.risk_run
                    if hasattr(risk_run, 'input_data'):
                        policy_terms = risk_run.input_data or {}
                    if hasattr(risk_run, 'result'):
                        risk_snapshot = risk_run.result or {}
                
                # Get FNOL data
                fnol = claim.fnol_json if hasattr(claim, 'fnol_json') else {}
                
                # Parse dates
                shipment_date = None
                if hasattr(policy, 'effective_from'):
                    effective_from = policy.effective_from
                    if isinstance(effective_from, datetime):
                        shipment_date = effective_from.date()
                    elif isinstance(effective_from, date):
                        shipment_date = effective_from
                
                record = {
                    "shipment_date": shipment_date,
                    "origin_port": policy_terms.get("pol") or policy_terms.get("origin_port"),
                    "destination_port": policy_terms.get("pod") or policy_terms.get("destination_port"),
                    "carrier_code": policy_terms.get("carrier") or policy_terms.get("carrier_code"),
                    "cargo_type": policy_terms.get("cargo_type"),
                    "cargo_value_usd": (policy_terms.get("cargo_value", 0) or 0),
                    "container_count": policy_terms.get("container_count", 1),
                    "loss_type": fnol.get("loss_type") or fnol.get("incident_type"),
                    "loss_amount_usd": ((claim.approved_amount_cents or 0) if hasattr(claim, 'approved_amount_cents') else 0) / 100,
                    "loss_cause": fnol.get("loss_description") or fnol.get("cause") or fnol.get("description"),
                    "claim_status": "CLAIM_APPROVED" if (hasattr(claim, 'decision') and claim.decision == "APPROVED") else "CLAIM_DENIED",
                    "claim_paid_usd": 0,  # Would need to query payouts
                    "claim_date": claim.created_at.date() if hasattr(claim, 'created_at') and claim.created_at else None,
                    "claim_resolution_date": claim.closed_at.date() if hasattr(claim, 'closed_at') and claim.closed_at else None,
                    "risk_score_predicted": risk_snapshot.get("overall_risk_score") or risk_snapshot.get("risk_score"),
                    "model_version": str(policy.model_version_id) if hasattr(policy, 'model_version_id') and policy.model_version_id else None,
                }
                records.append(record)
            
            config = ImportConfig(
                source=DataSource.INTERNAL_CLAIMS,
                file_path=None,
                api_endpoint=None,
                api_key=None,
                field_mappings={},  # Already in our format
                outcome_mappings={},
                claim_status_mappings={},
            )
            
            return await self._import_records(records, config, source_ref="internal_claims")
            
        except ImportError as e:
            self.logger.warning(f"Claims models not available: {e}, skipping internal claims import")
            return ImportResult(
                source=DataSource.INTERNAL_CLAIMS,
                total_records=0,
                imported_records=0,
                skipped_records=0,
                error_records=0,
                errors=[{"error": f"Claims models not available: {e}"}],
                import_hash="",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Error importing internal claims: {e}")
            return ImportResult(
                source=DataSource.INTERNAL_CLAIMS,
                total_records=0,
                imported_records=0,
                skipped_records=0,
                error_records=1,
                errors=[{"error": str(e)}],
                import_hash="",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
    
    async def _fetch_from_api(
        self,
        config: ImportConfig,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data from API endpoint."""
        if not config.api_endpoint:
            return []
        
        try:
            headers = {}
            if config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            response = await self.client.get(
                config.api_endpoint,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different API response formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Try common keys
                return data.get("data", data.get("results", data.get("records", [])))
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching from API: {e}")
            return []
    
    def _map_fields(
        self,
        row: Dict[str, Any],
        config: ImportConfig
    ) -> Dict[str, Any]:
        """Map external fields to our schema."""
        mapped = {}
        
        # If no mappings, assume data is already in our format
        if not config.field_mappings:
            return row
        
        for source_field, our_field in config.field_mappings.items():
            if source_field in row:
                value = row[source_field]
                
                # Skip empty values
                if value is None or value == "":
                    continue
                
                # Parse dates
                if our_field.endswith("_date") or our_field == "shipment_date" or our_field == "outcome_date":
                    try:
                        if isinstance(value, str):
                            value = datetime.strptime(value, config.date_format).date()
                        elif isinstance(value, date):
                            pass  # Already a date
                        elif isinstance(value, datetime):
                            value = value.date()
                    except (ValueError, TypeError) as e:
                        self.logger.debug(f"Could not parse date {value}: {e}")
                        value = None
                
                # Parse numbers
                elif our_field.endswith("_usd") or our_field.endswith("_days") or our_field.endswith("_nm") or our_field.endswith("_kg"):
                    try:
                        if isinstance(value, str):
                            # Remove currency symbols and commas
                            value = value.replace("$", "").replace(",", "").strip()
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                
                elif our_field.endswith("_count") or our_field.endswith("_pct"):
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        try:
                            value = float(value) if value else None
                        except (ValueError, TypeError):
                            value = None
                
                mapped[our_field] = value
        
        return mapped
    
    def _determine_outcome(
        self,
        data: Dict[str, Any],
        config: ImportConfig
    ) -> ShipmentOutcome:
        """Determine shipment outcome from data."""
        # Check outcome mappings first
        raw_outcome = data.get("outcome") or data.get("loss_type") or data.get("status") or data.get("incident_type")
        if raw_outcome:
            # Try exact match
            if raw_outcome in config.outcome_mappings:
                return config.outcome_mappings[raw_outcome]
            
            # Try case-insensitive match
            raw_lower = str(raw_outcome).lower()
            for key, outcome in config.outcome_mappings.items():
                if key.lower() == raw_lower:
                    return outcome
        
        # Infer from loss data
        loss_amount = data.get("loss_amount_usd", 0) or 0
        cargo_value = data.get("cargo_value_usd", 0) or 0
        
        if loss_amount > 0:
            if cargo_value > 0:
                loss_pct = loss_amount / cargo_value
                if loss_pct >= 0.9:
                    return ShipmentOutcome.TOTAL_LOSS
                elif loss_pct >= 0.2:
                    return ShipmentOutcome.PARTIAL_LOSS
                elif loss_pct >= 0.05:
                    return ShipmentOutcome.DAMAGE_MAJOR
                else:
                    return ShipmentOutcome.DAMAGE_MINOR
            else:
                # If we have loss but no value, assume partial loss
                return ShipmentOutcome.PARTIAL_LOSS
        
        # Check for explicit loss indicators
        loss_type = data.get("loss_type", "").lower() if data.get("loss_type") else ""
        if "total" in loss_type or "complete" in loss_type:
            return ShipmentOutcome.TOTAL_LOSS
        if "partial" in loss_type:
            return ShipmentOutcome.PARTIAL_LOSS
        if "theft" in loss_type or "piracy" in loss_type:
            return ShipmentOutcome.THEFT
        if "damage" in loss_type:
            if "major" in loss_type or "severe" in loss_type:
                return ShipmentOutcome.DAMAGE_MAJOR
            else:
                return ShipmentOutcome.DAMAGE_MINOR
        
        # Infer from delay
        expected = data.get("expected_transit_days")
        actual = data.get("actual_transit_days")
        if expected and actual and actual > expected:
            return ShipmentOutcome.DELIVERED_LATE
        
        # Default to on-time delivery
        return ShipmentOutcome.DELIVERED_ON_TIME
    
    def _validate_record(
        self,
        data: Dict[str, Any],
        config: ImportConfig
    ) -> tuple[bool, List[str]]:
        """Validate a record for import."""
        errors = []
        
        # Required fields
        if not data.get("shipment_date"):
            errors.append("Missing shipment_date")
        if not data.get("origin_port"):
            errors.append("Missing origin_port")
        if not data.get("destination_port"):
            errors.append("Missing destination_port")
        if not data.get("cargo_type"):
            errors.append("Missing cargo_type")
        if not data.get("cargo_value_usd"):
            errors.append("Missing cargo_value_usd")
        
        # If requiring loss data
        if config.require_loss_data:
            if not data.get("loss_amount_usd") and not data.get("loss_type"):
                errors.append("Missing loss data (required for this source)")
        
        # Validate date ranges
        shipment_date = data.get("shipment_date")
        if shipment_date:
            if isinstance(shipment_date, date):
                # Check if date is reasonable (not too far in future, not too old)
                today = date.today()
                if shipment_date > today:
                    errors.append(f"shipment_date {shipment_date} is in the future")
                if shipment_date < date(1900, 1, 1):
                    errors.append(f"shipment_date {shipment_date} is too old")
        
        # Validate numeric fields
        cargo_value = data.get("cargo_value_usd")
        if cargo_value is not None:
            if cargo_value < 0:
                errors.append("cargo_value_usd cannot be negative")
            if cargo_value > 1e12:  # Sanity check
                errors.append("cargo_value_usd is unreasonably large")
        
        return len(errors) == 0, errors
    
    async def _import_records(
        self,
        records: List[Dict[str, Any]],
        config: ImportConfig,
        source_ref: str = ""
    ) -> ImportResult:
        """Import a list of records."""
        started_at = datetime.utcnow()
        
        imported = 0
        skipped = 0
        errors = []
        
        for i, record in enumerate(records):
            try:
                # Map fields if needed
                mapped = self._map_fields(record, config) if config.field_mappings else record
                
                # Validate
                is_valid, validation_errors = self._validate_record(mapped, config)
                if not is_valid:
                    skipped += 1
                    errors.append({
                        "index": i,
                        "errors": validation_errors,
                        "sample_data": {k: v for k, v in list(mapped.items())[:5]}  # Sample for debugging
                    })
                    continue
                
                # Determine outcome
                outcome = self._determine_outcome(mapped, config)
                
                # Map claim status if provided
                if "claim_status" in mapped and config.claim_status_mappings:
                    raw_status = mapped["claim_status"]
                    if raw_status in config.claim_status_mappings:
                        mapped["claim_status"] = config.claim_status_mappings[raw_status].value
                
                # Import
                await self.repository.ingest_shipment_outcome(
                    shipment_data=mapped,
                    outcome=outcome,
                    source=config.source.value,
                    source_reference=f"{source_ref}:record_{i}" if source_ref else f"record_{i}"
                )
                
                imported += 1
                
            except Exception as e:
                skipped += 1
                errors.append({
                    "index": i,
                    "error": str(e),
                    "sample_data": {k: v for k, v in list(record.items())[:5]} if isinstance(record, dict) else None
                })
                self.logger.error(f"Error importing record {i}: {e}")
        
        completed_at = datetime.utcnow()
        import_hash = hashlib.sha256(
            f"{config.source.value}:{started_at.isoformat()}:{imported}:{len(records)}".encode()
        ).hexdigest()[:16]
        
        result = ImportResult(
            source=config.source,
            total_records=len(records),
            imported_records=imported,
            skipped_records=skipped,
            error_records=len(errors),
            errors=errors[:100],  # Limit stored errors
            import_hash=import_hash,
            started_at=started_at,
            completed_at=completed_at
        )
        
        # Audit the import
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="DATA_IMPORT",
                    action="HISTORICAL_DATA_IMPORTED",
                    entity_type="import_batch",
                    entity_id=import_hash,
                    actor_type="SYSTEM",
                    payload={
                        "source": config.source.value,
                        "source_ref": source_ref,
                        "total": len(records),
                        "imported": imported,
                        "skipped": skipped,
                        "errors": len(errors)
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit import: {e}")
        
        return result
    
    def _compute_import_hash(
        self,
        file_path: Path,
        config: ImportConfig,
        imported_count: int
    ) -> str:
        """Compute hash of import operation."""
        data = f"{file_path}:{config.source.value}:{imported_count}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
