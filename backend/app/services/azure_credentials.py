"""
Centralized Azure credential management for Container Apps with managed identity and API key support
"""
import os
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.core.credentials import AzureKeyCredential
import logging

logger = logging.getLogger(__name__)

def get_azure_credential():
    """
    Get Azure credential with support for managed identity (API key handled separately)
    
    Returns:
        Azure credential instance configured for the current environment
    """
    # Check if we have a user-assigned managed identity client ID
    managed_identity_client_id = os.getenv("AZURE_CLIENT_ID") or os.getenv("MANAGED_IDENTITY_CLIENT_ID")
    
    if managed_identity_client_id:
        logger.info(f"Using ManagedIdentityCredential with client_id: {managed_identity_client_id[:8]}...")
        try:
            # For user-assigned managed identity in Container Apps
            return ManagedIdentityCredential(client_id=managed_identity_client_id)
        except Exception as e:
            logger.warning(f"ManagedIdentityCredential failed: {e}, falling back to DefaultAzureCredential")
    
    # Fallback to DefaultAzureCredential with managed identity client ID if available
    if managed_identity_client_id:
        logger.info("Using DefaultAzureCredential with managed_identity_client_id")
        try:
            return DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
        except Exception as e:
            logger.warning(f"DefaultAzureCredential with client_id failed: {e}, using basic DefaultAzureCredential")
    
    # Final fallback - basic DefaultAzureCredential
    logger.info("Using basic DefaultAzureCredential")
    return DefaultAzureCredential()

def get_credential_for_azure_openai_direct():
    """
    Get credential for direct Azure OpenAI API calls - supports both API key and managed identity
    
    Returns:
        Credential for direct Azure OpenAI Client (supports both patterns)
    """
    # Check for API key first (easier deployment option)
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key and api_key != "placeholder-update-after-deployment":
        logger.info("Using API key authentication for direct Azure OpenAI")
        return AzureKeyCredential(api_key)
    
    # Fall back to managed identity
    logger.info("Using managed identity for direct Azure OpenAI")
    return get_azure_credential()

def get_credential_for_azure_ai_projects():
    """
    Get credential specifically for Azure AI Projects - ONLY supports token-based authentication
    
    Note: Azure AI Projects SDK does not support API key authentication directly.
    It only accepts TokenCredential implementations.
    
    Returns:
        TokenCredential for Azure AI Projects Client
    """
    # Azure AI Projects SDK ONLY supports token-based authentication
    # API keys are not supported - we must use managed identity or other token credential
    
    # Check if we have an API key but explain the limitation
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key and api_key != "placeholder-update-after-deployment":
        logger.warning("Azure AI Projects SDK does not support API key authentication directly")
        logger.warning("Falling back to managed identity authentication for AI Projects")
    
    # Always use token-based credential for Azure AI Projects
    logger.info("Using token-based authentication for Azure AI Projects")
    return get_azure_credential()

def get_credential_for_scope(scope: str = None):
    """
    Get credential and ensure it works for the specified scope
    
    Args:
        scope: Azure scope to test (optional)
    
    Returns:
        Working Azure credential
    """
    credential = get_azure_credential()
    
    # Test the credential if scope is provided
    if scope:
        try:
            token = credential.get_token(scope)
            logger.info(f"Credential successfully obtained token for scope: {scope}")
            return credential
        except Exception as e:
            logger.error(f"Credential failed for scope {scope}: {e}")
            # Return credential anyway - let the calling service handle the error
            return credential
    
    return credential
