import os
import logging
import asyncio
from dotenv import load_dotenv
from .azure_credentials import get_azure_ai_projects_client

logger = logging.getLogger(__name__)
load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("AGENT_NAME", "architectai-design-agent")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

cached_agent_id = None

def get_agents_client():
    """Get Azure AI Projects client - automatically chooses SDK or REST API based on authentication method"""
    if not PROJECT_ENDPOINT:
        raise ValueError("PROJECT_ENDPOINT environment variable is not configured. Please set up your Azure AI Foundry project endpoint.")
    
    if not PROJECT_ENDPOINT.startswith("https://"):
        raise ValueError(f"Invalid PROJECT_ENDPOINT format: {PROJECT_ENDPOINT}. Should start with https://")
    
    try:
        # This will automatically choose between SDK (managed identity) or REST API (API key)
        project_client = get_azure_ai_projects_client()
        logger.info(f"Created AI Projects client for endpoint: {PROJECT_ENDPOINT}")
        
        # Return the agents interface
        return project_client.agents
    except Exception as e:
        logger.error(f"Failed to create Azure AI Projects client: {e}")
        raise Exception(f"Failed to create Azure AI Projects client. Please check your PROJECT_ENDPOINT and authentication credentials. Error: {str(e)}")

async def get_or_create_agent():
    """Get or create the design agent"""
    global cached_agent_id
    if cached_agent_id:
        return cached_agent_id
    
    agents_client = get_agents_client()
    
    try:
        # List existing agents
        existing_agents_task = agents_client.list_agents()
        if asyncio.iscoroutine(existing_agents_task):
            existing_agents = await existing_agents_task
        else:
            existing_agents = existing_agents_task
            
        for agent in existing_agents:
            # Handle both object and dictionary formats
            agent_name = agent.get("name") if isinstance(agent, dict) else getattr(agent, "name", None)
            agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
            
            if agent_name == AGENT_NAME and agent_id:
                cached_agent_id = agent_id
                logger.info(f"Found existing agent: {agent_id}")
                return agent_id
    except Exception as e:
        logger.warning(f"Error listing agents: {e}")
    
    try:
        logger.info(f"Creating new agent: {AGENT_NAME}")
        
        # Create new agent
        create_agent_task = agents_client.create_agent(
            model=MODEL_NAME,
            name=AGENT_NAME,
            instructions="""You are an expert Azure Cloud Architect AI assistant. Your role is to analyze user requirements and design comprehensive, production-ready Azure cloud architectures.

Your expertise includes:
- Azure services and their optimal use cases
- Scalability, security, and cost optimization
- Modern application patterns (microservices, serverless, containers)
- Data architecture and analytics solutions
- DevOps and CI/CD pipelines
- Compliance and governance frameworks

Format your response with:
- Executive Summary
- Architecture Overview
- Service Recommendations with justifications
- Implementation Guidelines
- Security Considerations
- Cost Optimization Tips
- Next Steps

Be specific, actionable, and include Azure service names, SKUs when relevant, and configuration guidance.""",
            tools=["file_search", "code_interpreter"]  # Simplified tools format
        )
        
        if asyncio.iscoroutine(create_agent_task):
            agent = await create_agent_task
        else:
            agent = create_agent_task
        
        # Handle both object and dictionary formats for the created agent
        agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
        cached_agent_id = agent_id
        logger.info(f"Created new agent: {agent_id}")
        return agent_id
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        # Try with no tools as fallback
        try:
            logger.info(f"Retrying agent creation without tools...")
            create_agent_task = agents_client.create_agent(
                model=MODEL_NAME,
                name=AGENT_NAME,
                instructions="""You are an expert Azure Cloud Architect AI assistant. Your role is to analyze user requirements and design comprehensive, production-ready Azure cloud architectures.

Your expertise includes:
- Azure services and their optimal use cases
- Scalability, security, and cost optimization
- Modern application patterns (microservices, serverless, containers)
- Data architecture and analytics solutions
- DevOps and CI/CD pipelines
- Compliance and governance frameworks

Format your response with:
- Executive Summary
- Architecture Overview
- Service Recommendations with justifications
- Implementation Guidelines
- Security Considerations
- Cost Optimization Tips
- Next Steps

Be specific, actionable, and include Azure service names, SKUs when relevant, and configuration guidance."""
            )
            
            if asyncio.iscoroutine(create_agent_task):
                agent = await create_agent_task
            else:
                agent = create_agent_task
                
            agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
            cached_agent_id = agent_id
            logger.info(f"Created new agent without tools: {agent_id}")
            return agent_id
        except Exception as e2:
            logger.error(f"Error creating agent without tools: {e2}")
            raise

async def generate_design_document(user_input: str) -> str:
    """
    Generate a comprehensive Azure architecture design document using Azure AI Projects agent.
    
    Args:
        user_input: User's architecture requirement or scenario
        
    Returns:
        str: Detailed architecture design document
    """
    if not user_input or not user_input.strip():
        return "Error: No input provided for architecture design."
    
    if not PROJECT_ENDPOINT:
        return """Error: Azure AI Foundry project not configured.

To fix this issue:
1. Create an Azure AI Foundry project in the Azure portal
2. Update your Key Vault with the correct PROJECT_ENDPOINT value
3. Update your Key Vault with a valid AZURE_OPENAI_API_KEY
4. Restart the application

The PROJECT_ENDPOINT should look like: https://your-ai-foundry-project.services.ai.azure.com/api/projects/your-project"""
    
    try:
        agents_client = get_agents_client()
        agent_id = await get_or_create_agent()
        
        logger.info(f"Starting design generation for: {user_input[:100]}...")
        
        # Create thread
        thread_task = agents_client.threads.create()
        if asyncio.iscoroutine(thread_task):
            thread = await thread_task
        else:
            thread = thread_task
            
        thread_id = thread.get("id") if isinstance(thread, dict) else getattr(thread, "id", None)
        logger.info(f"Created thread: {thread_id}")
        
        # Create message
        message_task = agents_client.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"""Please design a comprehensive Azure cloud architecture for the following requirement:

**Requirement**: {user_input}

**Context**: This is for a production-ready solution that should follow Azure Well-Architected Framework principles. Please provide specific Azure service recommendations, configuration guidance, and implementation steps.

**Expected Output**: A detailed architecture design document with service justifications, security considerations, and deployment guidance."""
        )
        
        if asyncio.iscoroutine(message_task):
            await message_task
        else:
            pass  # Message created
        
        logger.info("Starting agent run...")
        
        # Create and process run
        run_task = agents_client.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
        if asyncio.iscoroutine(run_task):
            run = await run_task
        else:
            run = run_task
            
        run_status = run.get("status") if isinstance(run, dict) else getattr(run, "status", "unknown")
        logger.info(f"Agent run completed with status: {run_status}")
        
        # Get messages
        messages_task = agents_client.messages.list(thread_id=thread_id, order="desc")
        if asyncio.iscoroutine(messages_task):
            messages = await messages_task
        else:
            messages = list(messages_task)
            
        logger.info(f"Retrieved {len(messages)} messages")
        
        # Find the assistant's response
        for message in messages:
            message_role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
            message_content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
            
            if message_role == "assistant" and message_content:
                # Handle different content types
                content_parts = []
                
                if isinstance(message_content, str):
                    content_parts.append(message_content)
                elif isinstance(message_content, list):
                    for content_item in message_content:
                        if isinstance(content_item, dict):
                            if content_item.get("type") == "text":
                                text_obj = content_item.get("text", {})
                                if isinstance(text_obj, dict) and "value" in text_obj:
                                    content_parts.append(text_obj["value"])
                                elif isinstance(text_obj, str):
                                    content_parts.append(text_obj)
                        elif hasattr(content_item, 'text') and content_item.text:
                            content_parts.append(content_item.text.value)
                        elif hasattr(content_item, 'image_file'):
                            content_parts.append("[Image content - see attached diagram]")
                
                if content_parts:
                    result = "\n".join(content_parts)
                    logger.info(f"Generated design document ({len(result)} characters)")
                    return result
                
        return "No design document was generated. Please try again with a more specific requirement."
        
    except Exception as e:
        error_msg = f"""Error in design document generation: {str(e)}

If you're seeing authentication errors, please ensure:
1. Your Azure AI Foundry project endpoint is correctly configured
2. Your API key is valid and up to date
3. For API key authentication, the key has proper permissions

For troubleshooting, check the application logs for more details."""
        logger.error(error_msg)
        return error_msg