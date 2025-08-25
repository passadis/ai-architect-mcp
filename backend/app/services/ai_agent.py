import os
from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv
from .azure_credentials import get_credential_for_azure_ai_projects

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("AGENT_NAME", "architectai-design-agent")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

cached_agent_id = None

def get_agents_client():
    credential = get_credential_for_azure_ai_projects()
    project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)
    return project_client.agents

def get_or_create_agent():
    global cached_agent_id
    if cached_agent_id:
        return cached_agent_id
    
    agents_client = get_agents_client()
        
    try:
        existing_agents = agents_client.list_agents()
        for agent in existing_agents:
            if agent.name == AGENT_NAME:
                cached_agent_id = agent.id
                print(f"Found existing agent: {agent.id}")
                return agent.id
    except Exception as e:
        print(f"Error listing agents: {e}")
    
    try:
        print(f"Creating new agent: {AGENT_NAME}")
        agent = agents_client.create_agent(
            model=MODEL_NAME,
            name=AGENT_NAME,
            instructions="""You are an expert Azure Cloud Architect assistant. When provided with a requirement or scenario, you should:

1. **Analyze Requirements**: Understand the functional and non-functional requirements
2. **Design Architecture**: Recommend appropriate Azure services and patterns
3. **Consider Well-Architected Framework**: Apply reliability, security, cost optimization, operational excellence, and performance efficiency principles
4. **Provide Implementation Guidance**: Include configuration details, best practices, and deployment considerations
5. **Address Scalability**: Consider current and future scaling needs
6. **Security by Design**: Include identity, data protection, and network security recommendations

Format your response with:
- Executive Summary
- Architecture Overview
- Service Recommendations with justifications
- Implementation Guidelines
- Security Considerations
- Cost Optimization Tips
- Next Steps

Be specific, actionable, and include Azure service names, SKUs when relevant, and configuration guidance.""",
            tools=[
                {"type": "file_search"},
                {"type": "code_interpreter"}
            ],
            tool_resources={
                "file_search": {"vector_stores": []},
                "code_interpreter": {"file_ids": []}
            }
        )
        cached_agent_id = agent.id
        print(f"Created new agent: {agent.id}")
        return agent.id
    except Exception as e:
        print(f"Error creating agent: {e}")
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
        return "Error: PROJECT_ENDPOINT environment variable not configured."
    
    try:
        agents_client = get_agents_client()
        agent_id = get_or_create_agent()
        
        print(f"Starting design generation for: {user_input[:100]}...")
        
        thread = agents_client.threads.create()
        print(f"Created thread: {thread.id}")
        
        agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"""Please design a comprehensive Azure cloud architecture for the following requirement:

**Requirement**: {user_input}

**Context**: This is for a production-ready solution that should follow Azure Well-Architected Framework principles. Please provide specific Azure service recommendations, configuration guidance, and implementation steps.

**Expected Output**: A detailed architecture design document with service justifications, security considerations, and deployment guidance."""
        )
        
        print("Starting agent run...")
        run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent_id)
        print(f"Agent run completed: {run.id}")
        
        # Wait for completion and get messages
        messages = list(agents_client.messages.list(thread_id=thread.id, order="desc"))
        print(f"Retrieved {len(messages)} messages")
        
        # Find the assistant's response
        for message in messages:
            if message.role == "assistant" and hasattr(message, 'content') and message.content:
                # Handle different content types
                content_parts = []
                for content_item in message.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        content_parts.append(content_item.text.value)
                    elif hasattr(content_item, 'image_file'):
                        # Handle image content if present
                        content_parts.append("[Image content - see attached diagram]")
                
                if content_parts:
                    result = "\n".join(content_parts)
                    print(f"Generated design document ({len(result)} characters)")
                    return result
                
        return "No design document was generated. Please try again with a more specific requirement."
        
    except Exception as e:
        error_msg = f"Error in design document generation: {str(e)}"
        print(error_msg)
        return error_msg
