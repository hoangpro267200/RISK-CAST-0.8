"""
Model Versioning Service Usage Examples
RISKCAST V3 - Modular Monolith
"""
from datetime import datetime
from app.database import get_tenant_scoped_db, get_db
from app.modules.model_versioning.service import ModelVersionService
from app.modules.model_versioning.schemas import ModelVersionCreate, ActivationCreate
from app.modules.model_versioning.models import ModelScope
from app.modules.audit_ledger.schemas import AuditContext
from app.shared.dependencies import resolve_tenant_context
from fastapi import Request


async def example_create_and_publish_model():
    """Example: Create a draft model and publish it"""
    # Get tenant-scoped session (in real app, this comes from dependency injection)
    request = Request(...)  # FastAPI request
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        # Resolve tenant context
        context = await resolve_tenant_context(request, db_session, user=None)
        
        # Get tenant-scoped session
        db = await get_tenant_scoped_db(request, db_session)
        
        # Create service
        service = ModelVersionService(db)
        audit_context = AuditContext()
        
        # Create draft model
        create_data = ModelVersionCreate(
            name="Global Risk Model v1.0",
            scope=ModelScope.GLOBAL,
            weights_json={
                "route_layer": 0.4,
                "cargo_layer": 0.3,
                "climate_layer": 0.3
            },
            calibration_json={
                "alpha": 1.0,
                "beta": 0.5
            },
            constraints_json={
                "min_score": 0.0,
                "max_score": 1.0
            }
        )
        
        model = await service.create_draft(
            data=create_data,
            user_id=context.user_id,
            context=audit_context
        )
        
        print(f"Created draft model: {model.id}")
        
        # Publish model
        published_model = await service.publish(
            model_id=model.id,
            user_id=context.user_id,
            context=audit_context,
            reason="Initial release"
        )
        
        print(f"Published model: {published_model.id}, hash={published_model.immutable_hash}")
        
        # Try to update published model (should fail)
        try:
            from app.modules.model_versioning.schemas import ModelVersionUpdate
            update_data = ModelVersionUpdate(weights_json={"route_layer": 0.5})
            await service.update_draft(model.id, update_data, context.user_id, audit_context)
        except Exception as e:
            print(f"Expected error: {e}")  # ModelImmutableError
        
    finally:
        db_session.close()


async def example_resolve_model_for_run():
    """Example: Resolve active model for a risk run"""
    request = Request(...)
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        context = await resolve_tenant_context(request, db_session, user=None)
        db = await get_tenant_scoped_db(request, db_session)
        
        service = ModelVersionService(db)
        
        # Resolve model for a run
        model = await service.resolve_model_for_run(
            corridor_id="VN-US-WEST",
            product_type="standard",
            at_time=datetime.utcnow()
        )
        
        print(f"Resolved model: {model.id} ({model.name})")
        print(f"Model hash: {model.immutable_hash}")
        
    finally:
        db_session.close()


async def example_create_activation():
    """Example: Create model activation"""
    request = Request(...)
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        context = await resolve_tenant_context(request, db_session, user=None)
        db = await get_tenant_scoped_db(request, db_session)
        
        service = ModelVersionService(db)
        audit_context = AuditContext()
        
        # Create activation
        activation = await service.create_activation(
            model_version_id="model-version-id",
            corridor_id="VN-US-WEST",
            product_type="standard",
            effective_from=datetime.utcnow(),
            effective_to=None,  # Indefinite
            user_id=context.user_id,
            context=audit_context
        )
        
        print(f"Created activation: {activation.id}")
        
    finally:
        db_session.close()
