import os
import fsspec
import logging
import asyncio
from typing import BinaryIO, Optional, Union
from urllib.parse import urlparse
from flask import current_app, url_for
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
        
        # Set up logging - use Flask logger if in app context, otherwise use Python logging
        try:
            current_app.name  # Check if we're in app context
            self.logger = current_app.logger
        except RuntimeError:
            self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Initializing StorageBackend with URL: {storage_url}, protocol: {self.protocol}")
        
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
            self.logger.debug(f"Configured S3 storage with bucket: {self.bucket}, base_path: {self.base_path}")
        else:
            self.fs = fsspec.filesystem('file')
            self.base_path = self.parsed_url.path or '/uploads'
            self.logger.debug(f"Configured local storage with base_path: {self.base_path}")

    def _get_full_path(self, filename: str) -> str:
        """Get full path for a file"""
        if self.protocol == 's3':
            full_path = os.path.join(self.base_path, filename)
            self.logger.debug(f"Generated S3 full path: {full_path}")
            return full_path
        
        full_path = os.path.join(current_app.root_path, self.base_path, filename)
        self.logger.debug(f"Generated local full path: {full_path}")
        return full_path

    def save(self, file_storage: FileStorage, filename: str) -> str:
        """Save a file to storage"""
        try:
            full_path = self._get_full_path(filename)
            self.logger.info(f"Attempting to save file {filename} to {full_path}")
            
            if not isinstance(file_storage, FileStorage):
                self.logger.error(f"Invalid file_storage object type: {type(file_storage)}")
                raise ValueError("file_storage must be a FileStorage object")
            
            if self.protocol == 's3':
                s3_path = f"{self.bucket}/{full_path}"
                self.logger.debug(f"Opening S3 file for writing: {s3_path}")
                with self.fs.open(s3_path, 'wb') as f:
                    self.logger.debug("Saving file content to S3...")
                    file_storage.save(f)
                
                # Verify the file was saved
                if self.fs.exists(s3_path):
                    self.logger.info(f"Successfully saved file to S3: {s3_path}")
                else:
                    self.logger.error(f"Failed to verify file existence in S3: {s3_path}")
                    raise RuntimeError(f"Failed to verify file existence in S3: {s3_path}")
                
                return f"s3://{self.bucket}/{full_path}"
            else:
                # Create directory structure if it doesn't exist
                dir_path = os.path.dirname(full_path)
                self.logger.debug(f"Creating local directory structure: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
                
                self.logger.debug(f"Saving file to local path: {full_path}")
                file_storage.save(full_path)
                
                # Verify the file was saved
                if os.path.exists(full_path):
                    self.logger.info(f"Successfully saved file locally: {full_path}")
                    self.logger.debug(f"File size: {os.path.getsize(full_path)} bytes")
                else:
                    self.logger.error(f"Failed to verify file existence locally: {full_path}")
                    raise RuntimeError(f"Failed to verify file existence locally: {full_path}")
                
                return f"file://{full_path}"
                
        except Exception as e:
            self.logger.error(f"Error saving file {filename}: {str(e)}", exc_info=True)
            raise

    def open(self, filename: str, mode: str = 'rb') -> BinaryIO:
        """Open a file from storage"""
        full_path = self._get_full_path(filename)
        if self.protocol == 's3':
            return self.fs.open(f"{self.bucket}/{full_path}", mode)
        return self.fs.open(full_path, mode)

    def delete(self, filename: str) -> bool:
        """
        Delete a file from storage
        Returns True if file was deleted or didn't exist, False if deletion failed
        """
        try:
            full_path = self._get_full_path(filename)
            if self.protocol == 's3':
                path = f"{self.bucket}/{full_path}"
                self.logger.debug(f"Attempting to delete S3 file: {path}")
                if self.fs.exists(path):
                    self.logger.debug(f"File exists, deleting: {path}")
                    self.fs.delete(path)
                    deleted = not self.fs.exists(path)
                    if deleted:
                        self.logger.debug(f"Successfully deleted file: {path}")
                    else:
                        self.logger.error(f"Failed to delete file: {path}")
                    return deleted
                self.logger.debug(f"File doesn't exist, skipping delete: {path}")
                return True  # File didn't exist
            else:
                self.logger.debug(f"Attempting to delete local file: {full_path}")
                if self.fs.exists(full_path):
                    self.logger.debug(f"File exists, deleting: {full_path}")
                    self.fs.delete(full_path)
                    deleted = not os.path.exists(full_path)
                    if deleted:
                        self.logger.debug(f"Successfully deleted file: {full_path}")
                    else:
                        self.logger.error(f"Failed to delete file: {full_path}")
                    return deleted
                self.logger.debug(f"File doesn't exist, skipping delete: {full_path}")
                return True  # File didn't exist
        except Exception as e:
            self.logger.error(f"Failed to delete file {filename}: {str(e)}", exc_info=True)
            return False

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
            # For local storage, use static/uploads path
            return url_for('static', filename=f'uploads/{filename}')

    def exists(self, filename: str) -> bool:
        """Check if a file exists"""
        full_path = self._get_full_path(filename)
        if self.protocol == 's3':
            return self.fs.exists(f"{self.bucket}/{full_path}")
        return self.fs.exists(full_path) 