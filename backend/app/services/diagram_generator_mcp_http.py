import os
import json
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from .azure_credentials import get_credential_for_azure_ai_projects

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
AGENT_NAME = os.getenv("MCP_DIAGRAM_AGENT_NAME", "architectai-mcp-diagram-agent")
DIAGRAMS_OUTPUT_DIR = os.getenv("DIAGRAMS_OUTPUT_DIR", "static/diagrams")

DAPR_PORT = "3500"
DAPR_SERVICE_ID = "mcp-service"

# MCP HTTP service configuration
MCP_BASE_URL = f"http://localhost:{DAPR_PORT}/v1.0/invoke/{DAPR_SERVICE_ID}/method"
# MCP_HTTP_SERVICE_URL = os.getenv("MCP_SERVICE_URL") or os.getenv("MCP_HTTP_SERVICE_URL", "http://localhost:8001")
MCP_HTTP_TIMEOUT = int(os.getenv("MCP_HTTP_TIMEOUT", "60"))

_cached_agent_id = None

async def validate_components_via_mcp(component_names: list) -> Dict[str, Any]:
    """Validate Azure component names using MCP HTTP service"""
    try:
        async with httpx.AsyncClient(timeout=MCP_HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/mcp/tools/call",
                json={
                    "name": "validate_azure_components",
                    "arguments": {
                        "component_names": component_names
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "result" in data:
                    content = data["result"]["result"]["content"][0]["text"]
                    return json.loads(content)
            
            return {"validation_results": {}, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"validation_results": {}, "error": str(e)}

async def validate_import_statements_via_mcp(import_statements: list) -> Dict[str, Any]:
    """Validate import statements using MCP HTTP service"""
    try:
        # For now, let's build this validation logic using the existing component validation
        # and enhance it to check module paths
        
        invalid_imports = []
        
        for stmt in import_statements:
            module = stmt["module"]
            component = stmt["component"] 
            full_import = stmt["full_import"]
            
            # Validate the component exists
            component_result = await validate_components_via_mcp([component])
            
            if component_result.get("error"):
                invalid_imports.append({
                    "original_import": full_import,
                    "error": f"MCP service error: {component_result['error']}"
                })
                continue
            
            validation_results = component_result.get("validation_results", {})
            
            # Check if component is valid
            if component not in validation_results:
                invalid_imports.append({
                    "original_import": full_import,
                    "error": f"Component '{component}' not found in validation results"
                })
                continue
            
            component_info = validation_results[component]
            
            if not component_info.get("valid"):
                # Component doesn't exist at all
                invalid_imports.append({
                    "original_import": full_import,
                    "error": f"Component '{component}' does not exist",
                    "suggestions": component_info.get("suggestions", [])
                })
            else:
                # Component exists, but check if it's in the right module
                correct_module = component_info.get("submodule")
                if correct_module and correct_module != module:
                    suggested_import = f"from diagrams.azure.{correct_module} import {component}"
                    invalid_imports.append({
                        "original_import": full_import,
                        "suggested_import": suggested_import,
                        "error": f"Component '{component}' should be imported from '{correct_module}', not '{module}'"
                    })
        
        return {
            "invalid_imports": invalid_imports,
            "total_checked": len(import_statements),
            "errors_found": len(invalid_imports)
        }
            
    except Exception as e:
        return {"invalid_imports": [], "error": str(e)}

async def suggest_architecture_components_via_mcp(description: str, architecture_types: list = None) -> Dict[str, Any]:
    """Get architecture component suggestions using MCP HTTP service"""
    try:
        async with httpx.AsyncClient(timeout=MCP_HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/mcp/tools/call",
                json={
                    "name": "suggest_architecture_components",
                    "arguments": {
                        "description": description,
                        "architecture_types": architecture_types or ["frontend", "backend", "database", "cache"]
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "result" in data:
                    content = data["result"]["result"]["content"][0]["text"]
                    return json.loads(content)
            
            return {"suggestions": [], "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"suggestions": [], "error": str(e)}

async def generate_validated_diagram_via_mcp(description: str, provider: str = "azure", include_validation: bool = True) -> Dict[str, Any]:
    """Generate diagram with full validation using MCP HTTP service"""
    try:
        async with httpx.AsyncClient(timeout=MCP_HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/mcp/tools/call",
                json={
                    "name": "generate_validated_diagram",
                    "arguments": {
                        "description": description,
                        "provider": provider,
                        "include_validation": include_validation
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "result" in data:
                    content = data["result"]["result"]["content"][0]["text"]
                    return json.loads(content)
            
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

async def get_or_create_mcp_agent(client: AIProjectClient):
    """Get or create the MCP diagram agent"""
    global _cached_agent_id
    
    if _cached_agent_id:
        return _cached_agent_id
        
    try:
        existing_agents = client.agents.list_agents()
        for agent in existing_agents:
            if agent.name == AGENT_NAME:
                _cached_agent_id = agent.id
                print(f"Found existing MCP agent: {agent.id}")
                return agent.id
    except Exception as e:
        print(f"Error listing agents: {e}")
    
    # Create new agent
    try:
        print(f"Creating new MCP agent: {AGENT_NAME}")
        agent = client.agents.create_agent(
            model=MODEL_NAME,
            name=AGENT_NAME,
            instructions=(
                "You are an expert Azure architect and diagram generator. "
                "Use the available MCP tools to create and analyze architecture diagrams. "
                "Always provide detailed, professional responses with clear explanations."
            ),
            # No tools needed here - we'll call MCP directly
        )
        _cached_agent_id = agent.id
        print(f"Created MCP agent: {agent.id}")
        return agent.id
        
    except Exception as e:
        print(f"Error creating MCP agent: {e}")
        raise e

async def check_mcp_service_health():
    """Check if MCP HTTP service is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call an MCP tool via HTTP"""
    try:
        async with httpx.AsyncClient(timeout=MCP_HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/mcp/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP service error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise Exception(f"MCP tool error: {error}")
            
            return result.get("result", {})
            
    except Exception as e:
        print(f"Error calling MCP tool {tool_name}: {e}")
        raise e

async def generate_diagram_with_mcp_http(architecture_description: str) -> dict:
    """Generate architecture diagram using MCP HTTP service"""
    
    # Check if MCP service is available
    if not await check_mcp_service_health():
        raise Exception("MCP HTTP service is not available. Please ensure the MCP wrapper is running.")
    
    try:
        print("🔌 Using MCP HTTP service for diagram generation...")
        
        # Generate diagram using MCP HTTP service
        print("🎨 Generating diagram with MCP...")
        async with httpx.AsyncClient(timeout=MCP_HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/mcp/generate-diagram",
                json={
                    "architecture_description": architecture_description
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP diagram generation failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise Exception(f"MCP diagram generation error: {error}")
            
            mcp_result = result.get("result", {})
            
            # Extract the response content
            if "result" in mcp_result and "content" in mcp_result["result"]:
                content = mcp_result["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    # Get the text content
                    if hasattr(content[0], 'text'):
                        response_text = content[0].text
                    elif isinstance(content[0], dict) and "text" in content[0]:
                        response_text = content[0]["text"]
                    else:
                        response_text = str(content[0])
                else:
                    response_text = str(content)
                
                try:
                    # Try to parse as JSON
                    diagram_data = json.loads(response_text)
                    
                    # Ensure we have the required fields
                    result = {
                        "diagram_path": diagram_data.get("diagram_path", ""),
                        "diagram_code": diagram_data.get("diagram_code", ""),
                        "success": True,
                        "explanation": diagram_data.get("explanation", "Diagram generated successfully"),
                        "components_used": diagram_data.get("components_used", []),
                        "suggestions": diagram_data.get("suggestions", [])
                    }
                    
                    print(f"✅ MCP diagram generated: {result['diagram_path']}")
                    return result
                    
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text explanation
                    return {
                        "diagram_path": "",
                        "diagram_code": "",
                        "success": False,
                        "explanation": response_text,
                        "error": "Failed to parse diagram response as JSON"
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid response format from MCP service",
                    "explanation": str(mcp_result)
                }
            
    except Exception as e:
        print(f"Error in MCP HTTP diagram generation: {e}")
        return {
            "success": False,
            "error": str(e),
            "explanation": f"MCP diagram generation failed: {e}"
        }

async def analyze_architecture_with_mcp_http(diagram_code: str) -> dict:
    """Analyze architecture diagram using MCP HTTP service"""
    
    if not await check_mcp_service_health():
        raise Exception("MCP HTTP service is not available")
    
    try:
        print("🔍 Analyzing architecture with MCP HTTP service...")
        
        async with httpx.AsyncClient(timeout=MCP_HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/mcp/analyze-architecture",
                json={
                    "diagram_code": diagram_code
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP analysis failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise Exception(f"MCP analysis error: {error}")
            
            return result.get("result", {})
            
    except Exception as e:
        print(f"Error in MCP HTTP architecture analysis: {e}")
        raise e

# Legacy compatibility - map old function names to new HTTP-based ones
generate_diagram_with_mcp = generate_diagram_with_mcp_http
analyze_architecture_with_mcp = analyze_architecture_with_mcp_http
