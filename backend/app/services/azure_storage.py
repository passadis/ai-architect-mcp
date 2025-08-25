"""
Azure Storage Service for managing diagrams and static files
"""
import os
import logging
from datetime import datetime
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
import uuid

logger = logging.getLogger(__name__)

class AzureStorageService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "diagrams")
        self.use_managed_identity = os.getenv("AZURE_USE_MANAGED_IDENTITY", "false").lower() == "true"
        self.blob_service_client = None
        
        # Try to initialize with appropriate authentication
        self._initialize_client()
        
        # Skip container check during initialization to avoid authentication issues locally
        if self.blob_service_client:
            logger.info("Azure Storage service initialized - container will be created on first upload")

    def _reinitialize_with_connection_string(self):
        """Fallback to connection string authentication"""
        if self.connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                logger.info("Reinitialized Azure Storage with connection string")
            except Exception as e:
                logger.error(f"Failed to reinitialize with connection string: {e}")
                self.blob_service_client = None
        else:
            logger.error("No connection string available for fallback")
            self.blob_service_client = None

    def _initialize_client(self):
        """Initialize blob service client with fallback authentication"""
        if self.use_managed_identity:
            # Try managed identity first (for Azure Container Apps)
            try:
                account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
                if account_url:
                    from .azure_credentials import get_credential_for_scope
                    credential = get_credential_for_scope("https://storage.azure.com/.default")
                    self.blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
                    logger.info("Initialized Azure Storage with managed identity")
                    return
                else:
                    logger.warning("AZURE_STORAGE_ACCOUNT_URL not found, falling back to connection string")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure Storage with managed identity: {e}")
        
        # Fallback to connection string
        if self.connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                # Test the connection
                self.blob_service_client.get_account_information()
                logger.info("Initialized Azure Storage with connection string")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Storage with connection string: {e}")
                self.blob_service_client = None
        else:
            logger.warning("Azure Storage connection string not found, using local storage")
            self.blob_service_client = None
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container(public_access="blob")
                logger.info(f"Created container: {self.container_name}")
        except AzureError as e:
            logger.error(f"Error ensuring container exists: {e}")
    
    async def upload_diagram(self, file_path: str, filename: str = None) -> Optional[str]:
        """
        Upload diagram to Azure Storage
        Returns the blob URL if successful, None otherwise
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not configured, saving locally")
            return file_path
        
        try:
            if not filename:
                filename = f"diagram_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Ensure filename has proper extension
            if not filename.endswith('.png'):
                filename += '.png'

            # Ensure container exists before upload
            self._ensure_container_exists()
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=filename
            )
            
            # Upload file
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            # Return the blob URL
            blob_url = blob_client.url
            logger.info(f"Uploaded diagram to Azure Storage: {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading to Azure Storage: {e}")
            # If authentication fails, try to reinitialize with connection string
            if "ManagedIdentityCredential" in str(e) or "authentication" in str(e).lower():
                logger.info("Authentication failed, trying to reinitialize with connection string")
                try:
                    self._reinitialize_with_connection_string()
                    if self.blob_service_client:
                        # Ensure container exists
                        self._ensure_container_exists()
                        # Retry upload
                        blob_client = self.blob_service_client.get_blob_client(
                            container=self.container_name, 
                            blob=filename
                        )
                        with open(file_path, "rb") as data:
                            blob_client.upload_blob(data, overwrite=True)
                        blob_url = blob_client.url
                        logger.info(f"Uploaded diagram to Azure Storage after fallback: {blob_url}")
                        return blob_url
                except Exception as retry_error:
                    logger.error(f"Retry upload failed: {retry_error}")
            return None
            
        except AzureError as e:
            logger.error(f"Error uploading to Azure Storage: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
    
    async def download_diagram(self, blob_name: str, local_path: str) -> bool:
        """
        Download diagram from Azure Storage
        Returns True if successful, False otherwise
        """
        if not self.blob_service_client:
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            with open(local_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            logger.info(f"Downloaded diagram from Azure Storage: {blob_name}")
            return True
            
        except AzureError as e:
            logger.error(f"Error downloading from Azure Storage: {e}")
            return False
    
    async def list_diagrams(self) -> list:
        """
        List all diagrams in the container
        Returns list of blob names
        """
        if not self.blob_service_client:
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = container_client.list_blobs()
            return [blob.name for blob in blobs]
            
        except AzureError as e:
            logger.error(f"Error listing blobs: {e}")
            return []
    
    async def delete_diagram(self, blob_name: str) -> bool:
        """
        Delete diagram from Azure Storage
        Returns True if successful, False otherwise
        """
        if not self.blob_service_client:
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            blob_client.delete_blob()
            
            logger.info(f"Deleted diagram from Azure Storage: {blob_name}")
            return True
            
        except AzureError as e:
            logger.error(f"Error deleting from Azure Storage: {e}")
            return False

# Global instance
storage_service = AzureStorageService()
