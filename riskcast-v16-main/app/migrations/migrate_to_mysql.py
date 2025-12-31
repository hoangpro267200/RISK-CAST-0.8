"""
Migration Script: JSON Files → MySQL Database

This script migrates data from JSON files to MySQL database.
"""
import json
from pathlib import Path
from app.config.database import init_db, get_session
from app.models.shipment import ShipmentDB
from app.models.risk_analysis import RiskAnalysis
from app.models.scenario import Scenario
from app.models.kv_store import KVStore
from datetime import datetime
import uuid


def migrate_history_json():
    """Migrate data/history.json to MySQL"""
    history_file = Path("data/history.json")
    
    if not history_file.exists():
        print("⚠ No history.json file found - skipping migration")
        return 0
    
    print("📦 Migrating history.json to MySQL...")
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    migrated = 0
    with get_session() as db:
        for shipment_id, data in history.items():
            try:
                shipment_data = data.get("shipment_data", {})
                risk_analysis = data.get("risk_analysis", {})
                
                # Create shipment
                shipment = ShipmentDB(
                    id=str(uuid.uuid4()),
                    shipment_id=shipment_id,
                    pol=shipment_data.get("pol_code") or shipment_data.get("pol", ""),
                    pod=shipment_data.get("pod_code") or shipment_data.get("pod", ""),
                    route=shipment_data.get("route", ""),
                    carrier=shipment_data.get("carrier", ""),
                    etd=_parse_datetime(shipment_data.get("etd")),
                    eta=_parse_datetime(shipment_data.get("eta")),
                    cargo_type=shipment_data.get("cargo_type", ""),
                    cargo_value=str(shipment_data.get("cargo_value", "")),
                    shipment_data=shipment_data
                )
                db.add(shipment)
                
                # Create risk analysis
                risk_record = RiskAnalysis(
                    id=str(uuid.uuid4()),
                    shipment_id=shipment_id,
                    risk_score=risk_analysis.get("risk_score") or risk_analysis.get("overall_risk_index"),
                    overall_risk=risk_analysis.get("overall_risk_index") or risk_analysis.get("risk_score"),
                    risk_level=risk_analysis.get("risk_level", "MEDIUM"),
                    confidence=risk_analysis.get("confidence", 0.8),
                    engine_result=risk_analysis,
                    created_at=_parse_datetime(data.get("timestamp"))
                )
                db.add(risk_record)
                
                migrated += 1
                
            except Exception as e:
                print(f"⚠ Error migrating shipment {shipment_id}: {e}")
                continue
        
        db.commit()
    
    print(f"✅ Migrated {migrated} shipments from history.json")
    return migrated


def migrate_scenarios_json():
    """Migrate data/scenarios/scenarios.json to MySQL"""
    scenarios_file = Path("data/scenarios/scenarios.json")
    
    if not scenarios_file.exists():
        print("⚠ No scenarios.json file found - skipping migration")
        return 0
    
    print("📦 Migrating scenarios.json to MySQL...")
    
    with open(scenarios_file, 'r', encoding='utf-8') as f:
        scenarios_data = json.load(f)
    
    scenarios = scenarios_data.get("scenarios", {})
    migrated = 0
    
    with get_session() as db:
        for name, scenario_data in scenarios.items():
            try:
                scenario = Scenario(
                    id=str(uuid.uuid4()),
                    name=name,
                    adjustments=scenario_data.get("adjustments"),
                    result=scenario_data.get("result"),
                    baseline_score=str(scenario_data.get("baseline_score", "")),
                    description=scenario_data.get("description", ""),
                    category=scenario_data.get("category", "")
                )
                db.add(scenario)
                migrated += 1
                
            except Exception as e:
                print(f"⚠ Error migrating scenario {name}: {e}")
                continue
        
        db.commit()
    
    print(f"✅ Migrated {migrated} scenarios from scenarios.json")
    return migrated


def migrate_kv_store_json():
    """Migrate data/kv_store.json to MySQL"""
    kv_store_file = Path("data/kv_store.json")
    
    if not kv_store_file.exists():
        print("⚠ No kv_store.json file found - skipping migration")
        return 0
    
    print("📦 Migrating kv_store.json to MySQL...")
    
    with open(kv_store_file, 'r', encoding='utf-8') as f:
        kv_store = json.load(f)
    
    migrated = 0
    with get_session() as db:
        for key, value in kv_store.items():
            try:
                kv = KVStore(key=key, value=value)
                db.add(kv)
                migrated += 1
            except Exception as e:
                print(f"⚠ Error migrating key {key}: {e}")
                continue
        
        db.commit()
    
    print(f"✅ Migrated {migrated} key-value pairs from kv_store.json")
    return migrated


def _parse_datetime(dt_str: any) -> datetime:
    """Parse datetime string to datetime object"""
    if not dt_str:
        return datetime.utcnow()
    if isinstance(dt_str, datetime):
        return dt_str
    try:
        return datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
    except:
        return datetime.utcnow()


def main():
    """Run all migrations"""
    print("=" * 60)
    print("🚀 RISKCAST: JSON → MySQL Migration")
    print("=" * 60)
    print()
    
    # Initialize database (create tables)
    print("📋 Initializing database tables...")
    init_db()
    print("✅ Database tables created")
    print()
    
    # Run migrations
    total_migrated = 0
    total_migrated += migrate_history_json()
    print()
    total_migrated += migrate_scenarios_json()
    print()
    total_migrated += migrate_kv_store_json()
    print()
    
    print("=" * 60)
    print(f"✅ Migration complete! Total records migrated: {total_migrated}")
    print("=" * 60)


if __name__ == "__main__":
    main()

