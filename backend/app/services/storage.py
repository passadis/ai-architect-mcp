import json
import os
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Optional
import asyncio

# Import Azure services
from .azure_cosmos import cosmos_service
from .azure_storage import storage_service

# Fallback local data path
DATA_PATH = "data/architectures.json"

# Ensure the local data directory exists for fallback
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump([], f)

# Configuration
USE_AZURE_SERVICES = os.getenv("USE_AZURE_SERVICES", "true").lower() == "true"


async def load_architectures(user_id: str = "anonymous", limit: int = 50) -> List[Dict]:
    """Load architectures from Azure CosmosDB or local fallback"""
    if USE_AZURE_SERVICES:
        try:
            return await cosmos_service.list_architectures(user_id, limit)
        except Exception as e:
            print(f"Error loading from CosmosDB, using local fallback: {e}")
    
    # Local fallback
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

def load_architectures_sync():
    """Synchronous version for backwards compatibility"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(load_architectures())
    except RuntimeError:
        # No event loop running, use new one
        return asyncio.run(load_architectures())


async def save_architecture(title: str, preview: str, design_document: str, diagram_url: str, user_id: str = "anonymous") -> Dict:
    """Save architecture to Azure CosmosDB or local fallback"""
    
    # Check if architecture with same design document already exists
    items = await load_architectures(user_id)
    for item in items:
        if item.get("design_document") == design_document:
            # Return existing item instead of creating duplicate
            return {
                "id": item["id"],
                "title": item["title"],
                "preview": item["preview"],
                "design_document": item["design_document"],
                "diagram_url": item["diagram_url"],
                "timestamp": item.get("createdAt", item.get("timestamp")),
                "already_exists": True  # Flag to indicate it already existed
            }

    new_item = {
        "id": str(uuid4()),
        "title": title,
        "preview": preview,
        "design_document": design_document,
        "diagram_url": diagram_url,
        "timestamp": datetime.utcnow().isoformat(),
        "userId": user_id
    }

    if USE_AZURE_SERVICES:
        try:
            architecture_id = await cosmos_service.save_architecture(new_item)
            if architecture_id:
                new_item["id"] = architecture_id
                return new_item
        except Exception as e:
            print(f"Error saving to CosmosDB, using local fallback: {e}")
    
    # Local fallback
    items.insert(0, new_item)
    with open(DATA_PATH, "w") as f:
        json.dump(items, f, indent=2)

    return new_item

def save_architecture_sync(title: str, preview: str, design_document: str, diagram_url: str, user_id: str = "anonymous") -> Dict:
    """Synchronous version for backwards compatibility"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(save_architecture(title, preview, design_document, diagram_url, user_id))
    except RuntimeError:
        # No event loop running, use new one
        return asyncio.run(save_architecture(title, preview, design_document, diagram_url, user_id))

async def upload_diagram(file_path: str, filename: str = None) -> Optional[str]:
    """Upload diagram to Azure Storage or keep local"""
    if USE_AZURE_SERVICES:
        try:
            return await storage_service.upload_diagram(file_path, filename)
        except Exception as e:
            print(f"Error uploading to Azure Storage, keeping local: {e}")
    
    # Return local path if Azure Storage not available
    return file_path

async def get_architecture(architecture_id: str, user_id: str = "anonymous") -> Optional[Dict]:
    """Get architecture by ID from Azure CosmosDB or local fallback"""
    if USE_AZURE_SERVICES:
        try:
            return await cosmos_service.get_architecture(architecture_id, user_id)
        except Exception as e:
            print(f"Error getting from CosmosDB, using local fallback: {e}")
    
    # Local fallback
    items = await load_architectures()
    for item in items:
        if item.get("id") == architecture_id:
            return item
    return None

async def delete_architecture(architecture_id: str, user_id: str = "anonymous") -> bool:
    """Delete architecture from Azure CosmosDB or local fallback"""
    if USE_AZURE_SERVICES:
        try:
            return await cosmos_service.delete_architecture(architecture_id, user_id)
        except Exception as e:
            print(f"Error deleting from CosmosDB, using local fallback: {e}")
    
    # Local fallback
    items = await load_architectures()
    updated_items = [item for item in items if item.get("id") != architecture_id]
    if len(updated_items) < len(items):
        with open(DATA_PATH, "w") as f:
            json.dump(updated_items, f, indent=2)
        return True
    return False

async def check_architecture_exists(design_document: str, user_id: str = "anonymous") -> Optional[Dict]:
    """Check if architecture with same design document already exists"""
    items = await load_architectures(user_id)
    for item in items:
        if item.get("design_document") == design_document:
            return item
    return None


def check_architecture_exists_sync(design_document):
    """Check if an architecture with the same design document already exists (sync version)"""
    items = load_architectures_sync()
    for item in items:
        if item.get("design_document") == design_document:
            return item
    return None
