"""
Password Hashing Utilities

RISKCAST Auth System - Phase 1
Uses Argon2id for secure password hashing.
"""
import os
from typing import Optional

# Try to import argon2, fallback to bcrypt if unavailable
try:
    from argon2 import PasswordHasher as Argon2Hasher
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    try:
        import bcrypt
        BCrypt_AVAILABLE = True
    except ImportError:
        BCrypt_AVAILABLE = False

# Password validation
import re


class PasswordHasher:
    """
    Password hashing utility with Argon2id (preferred) or bcrypt (fallback).
    """
    
    def __init__(self):
        if ARGON2_AVAILABLE:
            # Argon2id configuration (memory-hard, resistant to GPU attacks)
            from argon2 import PasswordHasher as Argon2Hasher
            self.hasher = Argon2Hasher(
                time_cost=2,          # Number of iterations
                memory_cost=65536,     # 64 MB memory
                parallelism=4,       # Number of threads
                hash_len=32,          # Hash length
                salt_len=16          # Salt length
            )
            self.algorithm = "argon2id"
        elif BCrypt_AVAILABLE:
            self.hasher = bcrypt
            self.algorithm = "bcrypt"
        else:
            raise RuntimeError(
                "No password hashing library available. "
                "Install 'argon2-cffi' or 'bcrypt': pip install argon2-cffi"
            )
    
    def hash(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string (includes algorithm identifier)
        """
        if self.algorithm == "argon2id":
            # Argon2 returns hash directly
            return f"$argon2id${self.hasher.hash(password)}"
        else:
            # bcrypt
            salt = self.hasher.gensalt(rounds=12)
            hashed = self.hasher.hashpw(password.encode(), salt)
            return f"$bcrypt${hashed.decode()}"
    
    def verify(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Plain text password
            password_hash: Stored password hash (with algorithm prefix)
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            if password_hash.startswith("$argon2id$"):
                # Remove prefix and verify
                actual_hash = password_hash.replace("$argon2id$", "", 1)
                self.hasher.verify(actual_hash, password)
                return True
            elif password_hash.startswith("$bcrypt$"):
                # Remove prefix and verify
                actual_hash = password_hash.replace("$bcrypt$", "", 1)
                return self.hasher.checkpw(password.encode(), actual_hash.encode())
            else:
                # Legacy format (assume argon2)
                if ARGON2_AVAILABLE:
                    self.hasher.verify(password_hash, password)
                    return True
                return False
        except Exception:
            # Catch all exceptions (VerifyMismatchError, ValueError, etc.)
            return False


# Global instance
_password_hasher: Optional[PasswordHasher] = None


def get_password_hasher() -> PasswordHasher:
    """Get or create the global password hasher instance."""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = PasswordHasher()
    return _password_hasher


def hash_password(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return get_password_hasher().hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password
        password_hash: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    return get_password_hasher().verify(password, password_hash)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Args:
        password: Password to validate
        
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "Password must contain at least one special character"
    
    return True, None
