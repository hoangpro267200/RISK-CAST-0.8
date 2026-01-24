"""
Evidence Storage Abstraction
Abstract base class and implementations for evidence storage (local, S3, etc.)
"""
from __future__ import annotations

import os
import hashlib
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EvidenceStorage(ABC):
    """Abstract base class for evidence storage backends"""
    
    @abstractmethod
    def upload(self, content: bytes, path: str) -> str:
        """
        Upload content to storage.
        
        Args:
            content: Content bytes to upload
            path: Storage path (relative to storage root)
            
        Returns:
            Storage URI (e.g., 'file:///path/to/file' or 's3://bucket/path')
        """
        pass
    
    @abstractmethod
    def download(self, uri: str) -> bytes:
        """
        Download content from storage.
        
        Args:
            uri: Storage URI
            
        Returns:
            Content bytes
        """
        pass
    
    @abstractmethod
    def delete(self, uri: str) -> bool:
        """
        Delete content from storage.
        
        Args:
            uri: Storage URI
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, uri: str) -> bool:
        """
        Check if content exists in storage.
        
        Args:
            uri: Storage URI
            
        Returns:
            True if exists, False otherwise
        """
        pass


class LocalEvidenceStorage(EvidenceStorage):
    """Local filesystem storage implementation"""
    
    def __init__(self, base_path: str = "storage/evidence"):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory for storing evidence files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, content: bytes, path: str) -> str:
        """Upload content to local filesystem"""
        # Normalize path (remove leading slashes, handle relative paths)
        normalized_path = path.lstrip('/')
        full_path = self.base_path / normalized_path
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        full_path.write_bytes(content)
        
        # Return file:// URI
        return f"file://{full_path.absolute()}"
    
    def download(self, uri: str) -> bytes:
        """Download content from local filesystem"""
        if not uri.startswith("file://"):
            raise ValueError(f"Invalid file URI: {uri}")
        
        file_path = Path(uri[7:])  # Remove 'file://' prefix
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return file_path.read_bytes()
    
    def delete(self, uri: str) -> bool:
        """Delete content from local filesystem"""
        if not uri.startswith("file://"):
            raise ValueError(f"Invalid file URI: {uri}")
        
        file_path = Path(uri[7:])  # Remove 'file://' prefix
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {uri}: {e}")
            return False
    
    def exists(self, uri: str) -> bool:
        """Check if file exists"""
        if not uri.startswith("file://"):
            return False
        
        file_path = Path(uri[7:])  # Remove 'file://' prefix
        return file_path.exists()


class S3EvidenceStorage(EvidenceStorage):
    """AWS S3 storage implementation"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        """
        Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            aws_access_key_id: AWS access key ID (optional, uses credentials chain if not provided)
            aws_secret_access_key: AWS secret access key (optional, uses credentials chain if not provided)
        """
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        if aws_access_key_id and aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        else:
            # Use default credentials chain (environment variables, IAM role, etc.)
            self.s3_client = boto3.client('s3', region_name=region)
    
    def upload(self, content: bytes, path: str) -> str:
        """Upload content to S3"""
        # Normalize path (remove leading slashes)
        normalized_path = path.lstrip('/')
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=normalized_path,
                Body=content
            )
            
            # Return s3:// URI
            return f"s3://{self.bucket_name}/{normalized_path}"
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise
    
    def download(self, uri: str) -> bytes:
        """Download content from S3"""
        if not uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {uri}")
        
        # Parse s3://bucket/key
        parts = uri[5:].split('/', 1)  # Remove 's3://' prefix
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {uri}")
        
        bucket = parts[0]
        key = parts[1]
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except self.s3_client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"Object not found in S3: {uri}")
        except Exception as e:
            logger.error(f"Error downloading from S3: {e}")
            raise
    
    def delete(self, uri: str) -> bool:
        """Delete content from S3"""
        if not uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {uri}")
        
        # Parse s3://bucket/key
        parts = uri[5:].split('/', 1)  # Remove 's3://' prefix
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {uri}")
        
        bucket = parts[0]
        key = parts[1]
        
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            return False
    
    def exists(self, uri: str) -> bool:
        """Check if object exists in S3"""
        if not uri.startswith("s3://"):
            return False
        
        # Parse s3://bucket/key
        parts = uri[5:].split('/', 1)  # Remove 's3://' prefix
        if len(parts) != 2:
            return False
        
        bucket = parts[0]
        key = parts[1]
        
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
