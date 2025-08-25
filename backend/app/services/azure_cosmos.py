"""
Azure CosmosDB Service for managing architecture documents
"""
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
import uuid

logger = logging.getLogger(__name__)

class AzureCosmosService:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        self.key = os.getenv("AZURE_COSMOS_KEY")
        self.database_name = os.getenv("AZURE_COSMOS_DATABASE_NAME", "ai-architect-db")
        self.container_name = os.getenv("AZURE_COSMOS_CONTAINER_NAME", "architectures")
        self.use_managed_identity = os.getenv("AZURE_USE_MANAGED_IDENTITY", "false").lower() == "true"
        
        # Initialize container to None first
        self.container = None
        self.client = None
        
        if self.use_managed_identity:
            # Use managed identity for authentication (Azure Container Apps)
            try:
                from .azure_credentials import get_credential_for_scope
                credential = get_credential_for_scope("https://cosmos.azure.com/.default")
                self.client = CosmosClient(url=self.endpoint, credential=credential)
                logger.info("Initialized CosmosDB with managed identity")
            except Exception as e:
                logger.warning(f"Failed to initialize CosmosDB with managed identity: {e}")
                # Fallback to key-based authentication
                if self.endpoint and self.key:
                    logger.info("Falling back to key-based authentication for CosmosDB")
                    try:
                        self.client = CosmosClient(url=self.endpoint, credential=self.key)
                    except Exception as key_error:
                        logger.error(f"Failed to initialize CosmosDB with key: {key_error}")
                else:
                    logger.warning("No CosmosDB key available for fallback")
        else:
            # Use key-based authentication
            if not self.endpoint or not self.key:
                logger.warning("CosmosDB credentials not found, using local storage")
            else:
                try:
                    self.client = CosmosClient(url=self.endpoint, credential=self.key)
                    logger.info("Initialized CosmosDB with key-based authentication")
                except Exception as e:
                    logger.warning(f"Failed to initialize CosmosDB with key: {e}")
        
        # Initialize database and container
        if self.client:
            self._initialize_database()
    
    def _initialize_database(self):
        """Create database and container if they don't exist"""
        try:
            # Create database if it doesn't exist
            database = self.client.create_database_if_not_exists(id=self.database_name)
            
            # Create container if it doesn't exist
            container = database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/userId"),
                offer_throughput=400  # Minimum throughput
            )
            
            self.container = container
            logger.info(f"Initialized CosmosDB: {self.database_name}/{self.container_name}")
            
        except AzureError as e:
            logger.error(f"Error initializing CosmosDB: {e}")
            self.container = None
    
    async def save_architecture(self, architecture_data: Dict) -> Optional[str]:
        """
        Save architecture document to CosmosDB
        Returns document ID if successful, None otherwise
        """
        if not self.container:
            logger.warning("CosmosDB not configured, saving locally")
            return self._save_locally(architecture_data)
        
        try:
            # Ensure required fields
            if "id" not in architecture_data:
                architecture_data["id"] = str(uuid.uuid4())
            
            if "userId" not in architecture_data:
                architecture_data["userId"] = "anonymous"
            
            architecture_data["createdAt"] = datetime.utcnow().isoformat()
            architecture_data["updatedAt"] = datetime.utcnow().isoformat()
            
            # Save to CosmosDB
            response = self.container.create_item(body=architecture_data)
            
            logger.info(f"Saved architecture to CosmosDB: {response['id']}")
            return response["id"]
            
        except AzureError as e:
            logger.error(f"Error saving to CosmosDB: {e}")
            return None
    
    async def get_architecture(self, architecture_id: str, user_id: str = "anonymous") -> Optional[Dict]:
        """
        Get architecture document from CosmosDB
        Returns document if found, None otherwise
        """
        if not self.container:
            return self._get_locally(architecture_id)
        
        try:
            response = self.container.read_item(
                item=architecture_id,
                partition_key=user_id
            )
            
            logger.info(f"Retrieved architecture from CosmosDB: {architecture_id}")
            return response
            
        except AzureError as e:
            logger.error(f"Error retrieving from CosmosDB: {e}")
            return None
    
    async def list_architectures(self, user_id: str = "anonymous", limit: int = 50) -> List[Dict]:
        """
        List architecture documents for a user
        Returns list of documents
        """
        if not self.container:
            return self._list_locally()
        
        try:
            query = f"SELECT * FROM c WHERE c.userId = @userId ORDER BY c.updatedAt DESC OFFSET 0 LIMIT {limit}"
            items = list(self.container.query_items(
                query=query,
                parameters=[
                    {"name": "@userId", "value": user_id}
                ],
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Listed {len(items)} architectures for user: {user_id}")
            return items
            
        except AzureError as e:
            logger.error(f"Error listing from CosmosDB: {e}")
            return []
    
    async def update_architecture(self, architecture_id: str, architecture_data: Dict, user_id: str = "anonymous") -> bool:
        """
        Update architecture document in CosmosDB
        Returns True if successful, False otherwise
        """
        if not self.container:
            return self._update_locally(architecture_id, architecture_data)
        
        try:
            # Get existing document
            existing = await self.get_architecture(architecture_id, user_id)
            if not existing:
                return False
            
            # Update fields
            existing.update(architecture_data)
            existing["updatedAt"] = datetime.utcnow().isoformat()
            
            # Save updated document
            self.container.replace_item(
                item=architecture_id,
                body=existing
            )
            
            logger.info(f"Updated architecture in CosmosDB: {architecture_id}")
            return True
            
        except AzureError as e:
            logger.error(f"Error updating in CosmosDB: {e}")
            return False
    
    async def delete_architecture(self, architecture_id: str, user_id: str = "anonymous") -> bool:
        """
        Delete architecture document from CosmosDB
        Returns True if successful, False otherwise
        """
        if not self.container:
            return self._delete_locally(architecture_id)
        
        try:
            self.container.delete_item(
                item=architecture_id,
                partition_key=user_id
            )
            
            logger.info(f"Deleted architecture from CosmosDB: {architecture_id}")
            return True
            
        except AzureError as e:
            logger.error(f"Error deleting from CosmosDB: {e}")
            return False
    
    # Local fallback methods (when CosmosDB is not available)
    def _save_locally(self, architecture_data: Dict) -> str:
        """Save architecture locally as fallback"""
        import json
        from pathlib import Path
        
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        architecture_id = str(uuid.uuid4())
        architecture_data["id"] = architecture_id
        architecture_data["createdAt"] = datetime.utcnow().isoformat()
        
        file_path = data_dir / f"{architecture_id}.json"
        with open(file_path, "w") as f:
            json.dump(architecture_data, f, indent=2)
        
        logger.info(f"Saved architecture locally: {architecture_id}")
        return architecture_id
    
    def _get_locally(self, architecture_id: str) -> Optional[Dict]:
        """Get architecture locally as fallback"""
        import json
        from pathlib import Path
        
        file_path = Path("data") / f"{architecture_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return None
    
    def _list_locally(self) -> List[Dict]:
        """List architectures locally as fallback"""
        import json
        from pathlib import Path
        
        data_dir = Path("data")
        if not data_dir.exists():
            return []
        
        architectures = []
        for file_path in data_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    architectures.append(data)
            except Exception as e:
                logger.error(f"Error reading local file {file_path}: {e}")
        
        return sorted(architectures, key=lambda x: x.get("createdAt", ""), reverse=True)
    
    def _update_locally(self, architecture_id: str, architecture_data: Dict) -> bool:
        """Update architecture locally as fallback"""
        existing = self._get_locally(architecture_id)
        if existing:
            existing.update(architecture_data)
            existing["updatedAt"] = datetime.utcnow().isoformat()
            self._save_locally(existing)
            return True
        return False
    
    def _delete_locally(self, architecture_id: str) -> bool:
        """Delete architecture locally as fallback"""
        from pathlib import Path
        
        file_path = Path("data") / f"{architecture_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

# Global instance
cosmos_service = AzureCosmosService()
