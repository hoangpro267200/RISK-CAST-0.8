"""
Audit Event Factory
"""

import factory
from factory import fuzzy
from datetime import datetime
from decimal import Decimal
import random
import hashlib
import json

try:
    from app.core.audit.immutable_ledger import AuditEventImmutable
except ImportError:
    AuditEventImmutable = None

from tests.factories.base import BaseFactory


# Event types
EVENT_TYPES = [
    "QUOTE_CREATED", "QUOTE_UPDATED", "QUOTE_ACCEPTED", "QUOTE_DECLINED", "QUOTE_BOUND",
    "POLICY_CREATED", "POLICY_UPDATED", "POLICY_CANCELLED", "POLICY_RENEWED",
    "CLAIM_FILED", "CLAIM_UPDATED", "CLAIM_APPROVED", "CLAIM_DENIED", "CLAIM_PAID",
    "CUSTOMER_CREATED", "CUSTOMER_UPDATED", "CUSTOMER_ACTIVATED", "CUSTOMER_SUSPENDED",
    "USER_LOGIN", "USER_LOGOUT", "USER_CREATED", "USER_UPDATED",
    "RISK_ASSESSMENT", "PRICING_CALCULATED",
    "MODEL_PUBLISHED", "MODEL_ACTIVATED",
    "PAYMENT_PROCESSED", "PAYMENT_FAILED"
]

# Actor types
ACTOR_TYPES = ["USER", "SYSTEM", "API", "ADMIN", "CRON"]


class AuditEventFactory(BaseFactory):
    """Factory for generating Audit Event test data."""
    
    class Meta:
        model = AuditEventImmutable
        skip_postgeneration_if_model_is_none = True
    
    # Event details
    event_type = fuzzy.FuzzyChoice(EVENT_TYPES)
    action = factory.LazyAttribute(lambda o: o.event_type.split("_")[1].lower())
    
    # Actor
    actor_type = fuzzy.FuzzyChoice(ACTOR_TYPES)
    actor_id = factory.LazyFunction(
        lambda: f"user-{random.randint(100, 999)}"
    )
    
    # Entity
    entity_type = factory.LazyAttribute(lambda o: o.event_type.split("_")[0].lower())
    entity_id = factory.LazyFunction(
        lambda: f"entity-{random.randint(1000, 9999)}"
    )
    
    # Event data
    event_data = factory.LazyFunction(lambda: {
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "user_agent": "Mozilla/5.0 (Test)",
        "changes": {
            "field": "status",
            "old_value": "PENDING",
            "new_value": "ACCEPTED"
        }
    })
    
    # Sequence and hash chain
    sequence_number = factory.Sequence(lambda n: n + 1)
    prev_hash = "0" * 64  # GENESIS_HASH
    event_hash = factory.LazyAttribute(
        lambda o: hashlib.sha256(
            json.dumps({
                "seq": o.sequence_number,
                "event_type": o.event_type,
                "entity_id": o.entity_id,
                "prev_hash": o.prev_hash
            }, sort_keys=True).encode()
        ).hexdigest()
    )
    
    # HMAC signature
    hmac_signature = factory.LazyFunction(
        lambda: hashlib.sha256(f"hmac-{random.randint(1, 100000)}".encode()).hexdigest()
    )
    
    # Tenant
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    # Timestamp
    created_at = factory.LazyFunction(datetime.utcnow)
    
    # Metadata
    metadata_json = factory.LazyFunction(lambda: {
        "request_id": f"req-{random.randint(100000, 999999)}",
        "session_id": f"sess-{random.randint(100000, 999999)}",
        "api_version": "v3"
    })
    
    class Params:
        """Traits for different event types."""
        
        # Quote events
        quote_created = factory.Trait(
            event_type="QUOTE_CREATED",
            action="created",
            entity_type="quote",
            event_data=factory.LazyFunction(lambda: {
                "cargo_value_usd": str(Decimal(random.randint(50000, 500000))),
                "origin_port": random.choice(["CNSHA", "USLAX", "NLRTM"]),
                "destination_port": random.choice(["USLAX", "NLRTM", "SGSIN"]),
                "cargo_type": random.choice(["ELECTRONICS", "MACHINERY"])
            })
        )
        
        quote_accepted = factory.Trait(
            event_type="QUOTE_ACCEPTED",
            action="accepted",
            entity_type="quote",
            event_data=factory.LazyFunction(lambda: {
                "accepted_by": f"user-{random.randint(100, 999)}",
                "acceptance_notes": "Quote accepted",
                "premium_usd": str(Decimal(random.randint(500, 5000)))
            })
        )
        
        # Policy events
        policy_created = factory.Trait(
            event_type="POLICY_CREATED",
            action="created",
            entity_type="policy",
            event_data=factory.LazyFunction(lambda: {
                "policy_number": f"POL-{random.randint(100000, 999999)}",
                "effective_from": datetime.utcnow().date().isoformat(),
                "coverage_limit_usd": str(Decimal(random.randint(100000, 1000000)))
            })
        )
        
        # Claim events
        claim_filed = factory.Trait(
            event_type="CLAIM_FILED",
            action="filed",
            entity_type="claim",
            event_data=factory.LazyFunction(lambda: {
                "claim_number": f"CLM-{random.randint(10000, 99999)}",
                "loss_type": random.choice(["CARGO_DAMAGE", "THEFT", "WATER_DAMAGE"]),
                "claimed_amount_usd": str(Decimal(random.randint(5000, 100000)))
            })
        )
        
        claim_approved = factory.Trait(
            event_type="CLAIM_APPROVED",
            action="approved",
            entity_type="claim",
            event_data=factory.LazyFunction(lambda: {
                "approved_by": f"adj-{random.randint(100, 999)}",
                "approved_amount_usd": str(Decimal(random.randint(5000, 100000))),
                "adjuster_notes": "Claim approved after review"
            })
        )
        
        # User events
        user_login = factory.Trait(
            event_type="USER_LOGIN",
            action="login",
            entity_type="user",
            actor_type="USER",
            event_data=factory.LazyFunction(lambda: {
                "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "user_agent": "Mozilla/5.0 (Test)",
                "login_method": "email_password"
            })
        )
        
        # System events
        system_event = factory.Trait(
            actor_type="SYSTEM",
            actor_id="system",
            event_data=factory.LazyFunction(lambda: {
                "automated": True,
                "trigger": "scheduled_task"
            })
        )
        
        # API events
        api_event = factory.Trait(
            actor_type="API",
            actor_id=factory.LazyFunction(lambda: f"api-key-{random.randint(1000, 9999)}"),
            event_data=factory.LazyFunction(lambda: {
                "api_version": "v3",
                "endpoint": "/api/v3/quotes/request",
                "method": "POST"
            })
        )
        
        # Risk assessment
        risk_assessment = factory.Trait(
            event_type="RISK_ASSESSMENT",
            action="assessed",
            entity_type="risk_run",
            event_data=factory.LazyFunction(lambda: {
                "risk_score": round(random.uniform(0.1, 0.9), 2),
                "risk_grade": random.choice(["A", "B", "C", "D", "F"]),
                "model_version": f"v{random.randint(1, 10)}.0.0"
            })
        )
        
        # Payment events
        payment_processed = factory.Trait(
            event_type="PAYMENT_PROCESSED",
            action="processed",
            entity_type="payment",
            event_data=factory.LazyFunction(lambda: {
                "amount_usd": str(Decimal(random.randint(100, 10000))),
                "payment_method": "WIRE_TRANSFER",
                "payment_reference": f"PAY-{random.randint(100000, 999999)}"
            })
        )
