import os
import fsspec
import asyncio
from typing import BinaryIO, Optional, Union
from urllib.parse import urlparse
from flask import current_app
from werkzeug.datastructures import FileStorage

class StorageBackend:
    def __init__(self, storage_url: str):
        """
        Initialize storage backend with a URL.
        Examples:
            - file:///path/to/storage (local filesystem)
            - s3://bucket-name/path (S3 compatible)
        """
        self.storage_url = storage_url
        self.parsed_url = urlparse(storage_url)
        self.protocol = self.parsed_url.scheme or 'file'
        
        # Configure filesystem
        if self.protocol == 's3':
            self.fs = fsspec.filesystem(
                's3',
                key=os.getenv('S3_ACCESS_KEY'),
                secret=os.getenv('S3_SECRET_KEY'),
                endpoint_url=os.getenv('S3_ENDPOINT_URL'),
                client_kwargs={
                    'endpoint_url': os.getenv('S3_ENDPOINT_URL')
                } if os.getenv('S3_ENDPOINT_URL') else None
            )
            self.bucket = self.parsed_url.netloc
            self.base_path = self.parsed_url.path.lstrip('/')
        else:
            self.fs = fsspec.filesystem('file')
            self.base_path = self.parsed_url.path or '/uploads'

    def _get_full_path(self, filename: str) -> str:
        """Get full path for a file"""
        if self.protocol == 's3':
            return os.path.join(self.base_path, filename)
        return os.path.join(current_app.root_path, self.base_path, filename)

    def save(self, file_storage: FileStorage, filename: str) -> str:
        """Save a file to storage"""
        full_path = self._get_full_path(filename)
        
        if self.protocol == 's3':
            with self.fs.open(f"{self.bucket}/{full_path}", 'wb') as f:
                file_storage.save(f)
            return f"s3://{self.bucket}/{full_path}"
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            file_storage.save(full_path)
            return f"file://{full_path}"

    def open(self, filename: str, mode: str = 'rb') -> BinaryIO:
        """Open a file from storage"""
        full_path = self._get_full_path(filename)
        if self.protocol == 's3':
            return self.fs.open(f"{self.bucket}/{full_path}", mode)
        return self.fs.open(full_path, mode)

    def delete(self, filename: str) -> None:
        """Delete a file from storage"""
        full_path = self._get_full_path(filename)
        if self.protocol == 's3':
            self.fs.delete(f"{self.bucket}/{full_path}")
        else:
            self.fs.delete(full_path)

    def url_for(self, filename: str) -> str:
        """Get URL for a file"""
        if self.protocol == 's3':
            full_path = self._get_full_path(filename)
            if os.getenv('S3_PUBLIC_URL'):
                # For public buckets with a custom domain
                return f"{os.getenv('S3_PUBLIC_URL')}/{full_path}"
            elif os.getenv('S3_ENDPOINT_URL'):
                # For MinIO/S3, construct direct URL
                endpoint = os.getenv('S3_ENDPOINT_URL').rstrip('/')
                return f"{endpoint}/{self.bucket}/{full_path}"
            return f"s3://{self.bucket}/{full_path}"
        else:
            return f"/uploads/{filename}"

    def exists(self, filename: str) -> bool:
        """Check if a file exists"""
        full_path = self._get_full_path(filename)
        if self.protocol == 's3':
            return self.fs.exists(f"{self.bucket}/{full_path}")
        return self.fs.exists(full_path) 