"""
Base Factory Configuration
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime, date, timedelta
import random
from decimal import Decimal


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""
    
    class Meta:
        abstract = True
        sqlalchemy_session = None  # Set in conftest
        sqlalchemy_session_persistence = "commit"


# Common data generators
class Generators:
    """Common data generators for factories."""
    
    PORTS = [
        "CNSHA", "CNNBO", "CNQIN", "HKHKG",
        "USLAX", "USNYC", "USOAK", "USSEA",
        "NLRTM", "DEHAM", "GBFXT", "FRLEH",
        "SGSIN", "MYPKG", "KRPUS", "JPYOK"
    ]
    
    CARGO_TYPES = [
        "ELECTRONICS", "MACHINERY", "TEXTILES",
        "FOOD_PERISHABLE", "FOOD_DRY", "CHEMICALS",
        "PHARMACEUTICALS", "AUTOMOTIVE", "RAW_MATERIALS", "GENERAL"
    ]
    
    CARRIERS = ["MAEU", "MSCU", "CMDU", "COSU", "EGLV", "HLCU", "ONEY", "YMLU"]
    
    LOSS_TYPES = [
        "CARGO_DAMAGE", "CARGO_LOSS", "CONTAMINATION",
        "THEFT", "WATER_DAMAGE", "FIRE", "COLLISION",
        "PIRACY", "DELAY", "PACKAGING_FAILURE"
    ]
    
    INDUSTRIES = [
        "LOGISTICS", "MANUFACTURING", "RETAIL", "TRADING",
        "E_COMMERCE", "AUTOMOTIVE", "PHARMACEUTICAL", "FOOD_BEVERAGE"
    ]
    
    @classmethod
    def random_port(cls):
        return random.choice(cls.PORTS)
    
    @classmethod
    def random_port_pair(cls):
        """Return a pair of different ports."""
        origin = random.choice(cls.PORTS)
        destination = random.choice([p for p in cls.PORTS if p != origin])
        return origin, destination
    
    @classmethod
    def random_cargo_type(cls):
        return random.choice(cls.CARGO_TYPES)
    
    @classmethod
    def random_carrier(cls):
        return random.choice(cls.CARRIERS)
    
    @classmethod
    def random_cargo_value(cls, min_val=50000, max_val=2000000):
        """Generate random cargo value in USD."""
        return Decimal(random.randint(min_val, max_val))
    
    @classmethod
    def random_risk_score(cls, min_score=0.1, max_score=0.9):
        """Generate random risk score between 0 and 1."""
        return round(random.uniform(min_score, max_score), 2)
    
    @classmethod
    def random_premium(cls, cargo_value):
        """Calculate random premium based on cargo value."""
        rate = Decimal(str(random.uniform(0.001, 0.005)))
        return (cargo_value * rate).quantize(Decimal("0.01"))
    
    @classmethod
    def future_date(cls, days_ahead_min=7, days_ahead_max=30):
        """Generate a future date."""
        days = random.randint(days_ahead_min, days_ahead_max)
        return date.today() + timedelta(days=days)
    
    @classmethod
    def past_date(cls, days_ago_min=1, days_ago_max=365):
        """Generate a past date."""
        days = random.randint(days_ago_min, days_ago_max)
        return date.today() - timedelta(days=days)
    
    @classmethod
    def random_email(cls, domain="example.com"):
        """Generate random email address."""
        username = f"user{random.randint(1000, 9999)}"
        return f"{username}@{domain}"
    
    @classmethod
    def random_phone(cls):
        """Generate random US phone number."""
        return f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    @classmethod
    def random_company_name(cls):
        """Generate random company name."""
        prefixes = ["Global", "International", "United", "Pacific", "Atlantic", "Premier"]
        middles = ["Shipping", "Logistics", "Trade", "Maritime", "Cargo", "Freight"]
        suffixes = ["Inc.", "LLC", "Corp.", "Ltd.", "Group"]
        
        return f"{random.choice(prefixes)} {random.choice(middles)} {random.choice(suffixes)}"
    
    @classmethod
    def risk_grade_from_score(cls, score):
        """Convert risk score to grade."""
        if score < 0.2:
            return "A"
        elif score < 0.4:
            return "B"
        elif score < 0.6:
            return "C"
        elif score < 0.8:
            return "D"
        else:
            return "F"
    
    @classmethod
    def credit_grade_from_score(cls, score):
        """Convert credit score to grade."""
        if score >= 80:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"
