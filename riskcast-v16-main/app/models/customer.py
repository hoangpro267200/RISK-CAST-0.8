"""
Customer Model

Represents a customer/company in the system.
Used for onboarding and account management.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.shared.models import BaseMixin


class Customer(Base, BaseMixin):
    """
    Customer/Company model.
    
    Represents a company that can purchase insurance.
    """
    __tablename__ = "customers"
    
    # ID, created_at, updated_at are inherited from BaseMixin
    
    # Company details
    company_name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(200), nullable=False)
    registration_number = Column(String(50), unique=True, nullable=False, index=True)
    tax_id = Column(String(50), nullable=True, index=True)
    
    # Address
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False, index=True)  # ISO country code
    
    # Contact
    primary_contact_name = Column(String(200), nullable=False)
    primary_contact_email = Column(String(255), nullable=False, index=True)
    primary_contact_phone = Column(String(50), nullable=False)
    
    # Business info
    industry = Column(String(100), nullable=False, index=True)
    annual_shipment_volume = Column(Integer, nullable=False)
    average_cargo_value_usd = Column(Float, nullable=False)
    primary_cargo_types = Column(JSON, nullable=True)  # List of cargo types
    primary_routes = Column(JSON, nullable=True)  # List of routes
    
    # Insurance history
    current_insurer = Column(String(200), nullable=True)
    years_insured = Column(Integer, nullable=False, default=0)
    claims_history_json = Column(JSON, nullable=True)  # {year: {count, amount}}
    
    # Onboarding
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    # PENDING, KYC_REQUIRED, KYC_VERIFIED, CREDIT_CHECK, APPROVED, REJECTED, ACTIVE
    onboarding_stage = Column(String(50), nullable=False, default="REGISTRATION")
    # REGISTRATION, REGISTRATION_COMPLETE, KYC_SUBMITTED, KYC_VERIFIED, KYC_FAILED, CREDIT_CHECK, CREDIT_ASSESSED, COMPLETE
    
    # KYC
    kyc_verified_at = Column(DateTime, nullable=True)
    kyc_verified_by_user_id = Column(String(26), ForeignKey('users.id'), nullable=True)
    
    # Credit assessment
    credit_score = Column(Integer, nullable=True)
    credit_grade = Column(String(1), nullable=True)  # A, B, C, D, F
    credit_limit_usd = Column(Float, nullable=True)
    credit_assessed_at = Column(DateTime, nullable=True)
    credit_assessed_by_user_id = Column(String(26), ForeignKey('users.id'), nullable=True)
    
    # Pricing
    pricing_tier = Column(String(20), nullable=True)  # STANDARD, PREFERRED, PREMIER, HIGH_RISK
    
    # Activation
    activated_at = Column(DateTime, nullable=True)
    activated_by_user_id = Column(String(26), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    kyc_documents = relationship("KYCDocumentModel", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, company_name={self.company_name}, status={self.status})>"


class KYCDocumentModel(Base, BaseMixin):
    """
    KYC Document model.
    
    Stores KYC documents submitted by customers.
    """
    __tablename__ = "kyc_documents"
    
    # ID, created_at, updated_at are inherited from BaseMixin
    
    customer_id = Column(String(26), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True)
    
    document_type = Column(String(100), nullable=False, index=True)
    # CERTIFICATE_OF_INCORPORATION, TAX_CERTIFICATE, PROOF_OF_ADDRESS, DIRECTOR_ID, W9, VAT_CERTIFICATE
    document_number = Column(String(100), nullable=False)
    issue_date = Column(String(50), nullable=False)
    expiry_date = Column(String(50), nullable=True)
    issuing_authority = Column(String(200), nullable=False)
    document_url = Column(String(500), nullable=False)  # S3 URL or file path
    
    # Verification
    status = Column(String(50), nullable=False, default="PENDING_VERIFICATION", index=True)
    # PENDING_VERIFICATION, VERIFIED, REJECTED
    verification_notes = Column(String(1000), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by_user_id = Column(String(26), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="kyc_documents")
    
    def __repr__(self):
        return f"<KYCDocumentModel(id={self.id}, customer_id={self.customer_id}, type={self.document_type}, status={self.status})>"
