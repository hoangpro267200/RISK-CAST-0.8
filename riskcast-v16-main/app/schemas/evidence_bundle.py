"""
Pydantic schemas for evidence bundles.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class BundleType(str, Enum):
    """Bundle type enumeration"""
    UNDERWRITING = "UNDERWRITING"
    CLAIM = "CLAIM"
    TRIGGER = "TRIGGER"
    ASSESSMENT = "ASSESSMENT"
    POLICY = "POLICY"
    EXPORT = "EXPORT"


class BundleStatus(str, Enum):
    """Bundle status enumeration"""
    OPEN = "OPEN"
    SEALED = "SEALED"
    ARCHIVED = "ARCHIVED"


class RetentionClass(str, Enum):
    """Retention class enumeration"""
    STANDARD = "STANDARD"       # 7 years
    REGULATORY = "REGULATORY"   # 10 years
    LEGAL_HOLD = "LEGAL_HOLD"   # Indefinite


class ItemRole(str, Enum):
    """Item role within bundle"""
    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    REFERENCE = "REFERENCE"


class LinkType(str, Enum):
    """Bundle link type"""
    PRIMARY = "PRIMARY"
    SUPPLEMENTARY = "SUPPLEMENTARY"
    REFERENCE = "REFERENCE"


# Request schemas
class BundleCreateRequest(BaseModel):
    """Request schema for creating a bundle"""
    name: Optional[str] = Field(None, max_length=255, description="Bundle name")
    description: Optional[str] = Field(None, description="Bundle description")
    bundle_type: BundleType = Field(..., description="Bundle type")
    retention_class: RetentionClass = Field(
        default=RetentionClass.STANDARD,
        description="Retention classification"
    )


class BundleItemAddRequest(BaseModel):
    """Request schema for adding an item to a bundle"""
    evidence_id: str = Field(..., description="Evidence object ID")
    role: ItemRole = Field(
        default=ItemRole.SUPPORTING,
        description="Item role within bundle"
    )
    description: Optional[str] = Field(None, description="Item description")


class BundleLinkRequest(BaseModel):
    """Request schema for linking a bundle to an entity"""
    entity_type: str = Field(..., max_length=100, description="Entity type")
    entity_id: str = Field(..., description="Entity ID")
    link_type: LinkType = Field(
        default=LinkType.PRIMARY,
        description="Link type"
    )


class BundleSealRequest(BaseModel):
    """Request to seal a bundle, making it immutable"""
    pass  # No additional fields needed


# Response schemas
class BundleItemResponse(BaseModel):
    """Response schema for bundle item"""
    id: str = Field(..., description="Item ID")
    evidence_id: str = Field(..., description="Evidence object ID")
    sequence: Optional[int] = Field(None, description="Order within bundle")
    role: Optional[str] = Field(None, description="Item role")
    description: Optional[str] = Field(None, description="Item description")
    content_hash_at_addition: str = Field(..., description="Content hash at time of addition")
    added_at: datetime = Field(..., description="When item was added")
    
    class Config:
        from_attributes = True


class BundleLinkResponse(BaseModel):
    """Response schema for bundle link"""
    id: str = Field(..., description="Link ID")
    entity_type: str = Field(..., description="Entity type")
    entity_id: str = Field(..., description="Entity ID")
    link_type: str = Field(..., description="Link type")
    created_at: datetime = Field(..., description="When link was created")
    
    class Config:
        from_attributes = True


class BundleManifest(BaseModel):
    """Bundle manifest structure"""
    items: List[Dict[str, Any]] = Field(..., description="List of items in manifest")
    item_count: int = Field(..., description="Number of items")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    sealed_at: Optional[datetime] = Field(None, description="When bundle was sealed")


class BundleResponse(BaseModel):
    """Response schema for bundle (summary)"""
    id: str = Field(..., description="Bundle ID")
    tenant_id: str = Field(..., description="Tenant ID")
    name: Optional[str] = Field(None, description="Bundle name")
    description: Optional[str] = Field(None, description="Bundle description")
    bundle_type: BundleType = Field(..., description="Bundle type")
    status: BundleStatus = Field(..., description="Bundle status")
    manifest_hash: Optional[str] = Field(None, description="Manifest hash")
    retention_class: str = Field(..., description="Retention classification")
    legal_hold: bool = Field(..., description="Whether bundle is on legal hold")
    contains_pii: bool = Field(..., description="Whether bundle contains PII")
    item_count: int = Field(default=0, description="Number of items in bundle")
    created_at: datetime = Field(..., description="Creation timestamp")
    sealed_at: Optional[datetime] = Field(None, description="Seal timestamp")
    
    class Config:
        from_attributes = True


class BundleDetailResponse(BundleResponse):
    """Response schema for bundle with full details"""
    manifest: Optional[BundleManifest] = Field(None, description="Bundle manifest")
    items: List[BundleItemResponse] = Field(default_factory=list, description="Bundle items")
    links: List[BundleLinkResponse] = Field(default_factory=list, description="Bundle links")
    pii_categories: Optional[List[str]] = Field(None, description="PII categories")
    
    class Config:
        from_attributes = True


class BundleExportResponse(BaseModel):
    """Response schema for bundle export"""
    bundle_id: str = Field(..., description="Bundle ID")
    manifest: BundleManifest = Field(..., description="Bundle manifest")
    manifest_hash: str = Field(..., description="Manifest hash")
    export_timestamp: datetime = Field(..., description="Export timestamp")
    verification_instructions: str = Field(..., description="Instructions for verifying bundle integrity")
    download_urls: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Download URLs for evidence objects"
    )
