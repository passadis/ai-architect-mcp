"""
Azure AI Projects REST API Client
Supports API key authentication for environments where Azure CLI/Managed Identity is not available
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class AzureAIProjectsRestClient:
    """
    REST API client for Azure AI Projects that supports API key authentication
    """
    
    def __init__(self, endpoint: str, api_key: str, api_version: str = "2024-12-01-preview"):
        """
        Initialize the REST client
        
        Args:
            endpoint: Azure AI Projects endpoint (e.g., https://your-project.services.ai.azure.com/api/projects/your-project)
            api_key: Azure OpenAI API key
            api_version: API version to use
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.api_version = api_version
        
        # Extract project ID from endpoint if present
        if '/projects/' in endpoint:
            self.project_id = endpoint.split('/projects/')[-1]
        else:
            self.project_id = "default"
        
        # Set up base headers
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "azure-ai-architect/1.0.0"
        }
        
        logger.info(f"Initialized Azure AI Projects REST client for endpoint: {endpoint}")
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents in the project"""
        url = f"{self.endpoint}/agents"
        params = {"api-version": self.api_version}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                agents = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"Retrieved {len(agents)} agents")
                return agents
                
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def create_agent(self, model: str, name: str, instructions: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new agent
        
        Args:
            model: Model deployment name
            name: Agent name
            instructions: Agent instructions
            tools: Optional list of tools (simplified format)
            
        Returns:
            Created agent data
        """
        url = f"{self.endpoint}/agents"
        params = {"api-version": self.api_version}
        
        # Build tools configuration
        tools_config = []
        if tools:
            for tool in tools:
                if tool == "file_search":
                    tools_config.append({"type": "file_search"})
                elif tool == "code_interpreter":
                    tools_config.append({"type": "code_interpreter"})
        
        payload = {
            "model": model,
            "name": name,
            "instructions": instructions,
            "tools": tools_config,
            "metadata": {
                "created_by": "azure-ai-architect",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self.headers, params=params, json=payload)
                response.raise_for_status()
                
                agent_data = response.json()
                logger.info(f"Created agent: {agent_data.get('id', 'unknown')}")
                return agent_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating agent: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to create agent: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    async def create_thread(self) -> Dict[str, Any]:
        """Create a new conversation thread"""
        url = f"{self.endpoint}/threads"
        params = {"api-version": self.api_version}
        
        payload = {
            "metadata": {
                "created_by": "azure-ai-architect",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, params=params, json=payload)
                response.raise_for_status()
                
                thread_data = response.json()
                logger.info(f"Created thread: {thread_data.get('id', 'unknown')}")
                return thread_data
                
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise
    
    async def create_message(self, thread_id: str, role: str, content: str) -> Dict[str, Any]:
        """Create a message in a thread"""
        url = f"{self.endpoint}/threads/{thread_id}/messages"
        params = {"api-version": self.api_version}
        
        payload = {
            "role": role,
            "content": content,
            "metadata": {
                "created_by": "azure-ai-architect",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, params=params, json=payload)
                response.raise_for_status()
                
                message_data = response.json()
                logger.info(f"Created message: {message_data.get('id', 'unknown')}")
                return message_data
                
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise
    
    async def create_and_process_run(self, thread_id: str, agent_id: str, additional_instructions: Optional[str] = None) -> Dict[str, Any]:
        """Create and process a run (simplified version that waits for completion)"""
        # Create run
        url = f"{self.endpoint}/threads/{thread_id}/runs"
        params = {"api-version": self.api_version}
        
        payload = {
            "assistant_id": agent_id,  # Note: Azure AI Projects uses "assistant_id"
            "additional_instructions": additional_instructions,
            "metadata": {
                "created_by": "azure-ai-architect",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Create the run
                response = await client.post(url, headers=self.headers, params=params, json=payload)
                response.raise_for_status()
                
                run_data = response.json()
                run_id = run_data.get('id')
                logger.info(f"Created run: {run_id}")
                
                # Poll for completion (simplified - in production, use proper polling with exponential backoff)
                max_attempts = 30
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)  # Wait 2 seconds between polls
                    
                    # Check run status
                    status_url = f"{self.endpoint}/threads/{thread_id}/runs/{run_id}"
                    status_response = await client.get(status_url, headers=self.headers, params=params)
                    status_response.raise_for_status()
                    
                    run_status = status_response.json()
                    status = run_status.get('status', 'unknown')
                    
                    logger.info(f"Run {run_id} status: {status}")
                    
                    if status in ['completed', 'failed', 'cancelled', 'expired']:
                        run_status['id'] = run_id
                        return run_status
                
                # Timeout
                logger.warning(f"Run {run_id} did not complete within {max_attempts * 2} seconds")
                return {"id": run_id, "status": "timeout", "last_error": "Run timed out"}
                
        except Exception as e:
            logger.error(f"Failed to create and process run: {e}")
            raise
    
    async def list_messages(self, thread_id: str, order: str = "desc") -> List[Dict[str, Any]]:
        """List messages in a thread"""
        url = f"{self.endpoint}/threads/{thread_id}/messages"
        params = {
            "api-version": self.api_version,
            "order": order,
            "limit": 20  # Reasonable limit
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                messages = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"Retrieved {len(messages)} messages from thread {thread_id}")
                return messages
                
        except Exception as e:
            logger.error(f"Failed to list messages: {e}")
            return []


# Remove the duplicate import
class AzureAIProjectsAdapter:
    """
    Adapter class that provides the same interface as the original SDK-based client
    """
    
    def __init__(self, rest_client: AzureAIProjectsRestClient):
        self.rest_client = rest_client
        self.agents = AgentsAdapter(rest_client)


class AgentsAdapter:
    """Adapter for agents operations"""
    
    def __init__(self, rest_client: AzureAIProjectsRestClient):
        self.rest_client = rest_client
        self.threads = ThreadsAdapter(rest_client)
        self.messages = MessagesAdapter(rest_client)
        self.runs = RunsAdapter(rest_client)
    
    def list_agents(self):
        """Return coroutine for list_agents"""
        return self.rest_client.list_agents()
    
    def create_agent(self, model: str, name: str, instructions: str, tools: Optional[List[str]] = None):
        """Return coroutine for create_agent"""
        return self.rest_client.create_agent(model, name, instructions, tools)


class ThreadsAdapter:
    """Adapter for threads operations"""
    
    def __init__(self, rest_client: AzureAIProjectsRestClient):
        self.rest_client = rest_client
    
    def create(self):
        """Create a new thread"""
        return self.rest_client.create_thread()


class MessagesAdapter:
    """Adapter for messages operations"""
    
    def __init__(self, rest_client: AzureAIProjectsRestClient):
        self.rest_client = rest_client
    
    def create(self, thread_id: str, role: str, content: str):
        """Create a message"""
        return self.rest_client.create_message(thread_id, role, content)
    
    def list(self, thread_id: str, order: str = "desc"):
        """List messages"""
        return self.rest_client.list_messages(thread_id, order)


class RunsAdapter:
    """Adapter for runs operations"""
    
    def __init__(self, rest_client: AzureAIProjectsRestClient):
        self.rest_client = rest_client
    
    def create_and_process(self, thread_id: str, agent_id: str, additional_instructions: Optional[str] = None):
        """Create and process a run"""
        return self.rest_client.create_and_process_run(thread_id, agent_id, additional_instructions)


def create_ai_projects_client(endpoint: str, api_key: str) -> AzureAIProjectsAdapter:
    """
    Factory function to create an Azure AI Projects client that supports API key authentication
    
    Args:
        endpoint: Azure AI Projects endpoint
        api_key: Azure OpenAI API key
        
    Returns:
        AzureAIProjectsAdapter that provides SDK-compatible interface
    """
    rest_client = AzureAIProjectsRestClient(endpoint, api_key)
    return AzureAIProjectsAdapter(rest_client)