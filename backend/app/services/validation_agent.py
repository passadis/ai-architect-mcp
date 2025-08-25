import os
import re
import json
import logging
import asyncio
from dotenv import load_dotenv
from .azure_credentials import get_azure_ai_projects_client

logger = logging.getLogger(__name__)

# Enhanced validation is handled through MCP service
# No local imports needed - all validation goes through MCP HTTP service
ENHANCED_VALIDATION_AVAILABLE = True  # Always available through MCP
logger.info("✅ Enhanced validation routed through MCP service")

load_dotenv()

# Load environment
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
VALIDATION_AGENT_NAME = os.getenv("VALIDATION_AGENT_NAME", "architectai-validation-agent")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# DAPR configuration for MCP service
DAPR_PORT = "3500"
DAPR_SERVICE_ID = "mcp-service"
MCP_BASE_URL = f"http://localhost:{DAPR_PORT}/v1.0/invoke/{DAPR_SERVICE_ID}/method"

# Global cache
_cached_validation_agent_id = None
_cached_validation_client = None


def get_validation_agents_client():
    """
    Get Azure AI Projects client for validation - automatically chooses SDK or REST API
    """
    global _cached_validation_client
    
    if _cached_validation_client:
        return _cached_validation_client.agents
    
    if not PROJECT_ENDPOINT:
        raise ValueError("PROJECT_ENDPOINT environment variable is not configured.")
    
    if not PROJECT_ENDPOINT.startswith("https://"):
        raise ValueError(f"Invalid PROJECT_ENDPOINT format: {PROJECT_ENDPOINT}. Should start with https://")
    
    try:
        # This will automatically choose between SDK (managed identity) or REST API (API key)
        _cached_validation_client = get_azure_ai_projects_client()
        logger.info(f"Created Validation AI Projects client for endpoint: {PROJECT_ENDPOINT}")
        return _cached_validation_client.agents
    except Exception as e:
        logger.error(f"Failed to create Azure AI Projects client for validation: {e}")
        raise Exception(f"Failed to create Azure AI Projects client for validation. Error: {str(e)}")


async def get_or_create_validation_agent():
    """
    Get or create the validation agent
    """
    global _cached_validation_agent_id
    
    if _cached_validation_agent_id:
        return _cached_validation_agent_id
    
    try:
        agents_client = get_validation_agents_client()
        
        # Check for existing agent
        existing_agents_task = agents_client.list_agents()
        if asyncio.iscoroutine(existing_agents_task):
            existing_agents = await existing_agents_task
        else:
            existing_agents = existing_agents_task
            
        for agent in existing_agents:
            # Handle both object and dictionary formats
            agent_name = agent.get("name") if isinstance(agent, dict) else getattr(agent, "name", None)
            agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
            
            if agent_name == VALIDATION_AGENT_NAME and agent_id:
                _cached_validation_agent_id = agent_id
                logger.info(f"Found existing validation agent: {agent_id}")
                return agent_id
    except Exception as e:
        logger.warning(f"Error listing validation agents: {e}")
    
    # Create new validation agent
    try:
        logger.info(f"Creating new validation agent: {VALIDATION_AGENT_NAME}")
        agents_client = get_validation_agents_client()
        
        # No tools needed - pure static analysis only
        instructions = (
            "You are a Python diagram code validator for Azure architecture diagrams. "
            "You MUST respond with valid JSON format only. Do NOT execute or test any code. "
            "Perform static analysis only.\n\n"
            
            "**STRICT REQUIREMENTS:**\n"
            "1. NEVER attempt to run, execute, or import the provided code\n"
            "2. NEVER mention missing libraries or installation issues\n"
            "3. ALWAYS respond with valid JSON format only\n"
            "4. Use static analysis and pattern matching to validate code\n\n"
            
            "**ENHANCED VALIDATION CAPABILITIES:**\n"
            "- Real-time Azure component validation using enhanced_azure_validator.py\n"
            "- Canonical name resolution (ACR → ContainerRegistries)\n"
            "- Submodule import validation (compute, web, database, etc.)\n"
            "- Alias detection and correction\n"
            "- Component availability checking\n\n"
            
            "**Common Import Fixes (apply based on static analysis):**\n"
            "- ResourceGroup → NOT AVAILABLE (remove completely)\n"
            "- AppService → AppServices (from diagrams.azure.web)\n"
            "- KeyVault → KeyVaults (from diagrams.azure.security)\n"
            "- StaticWebApps → NOT AVAILABLE (use AppServices instead)\n"
            "- ACR → ContainerRegistries (from diagrams.azure.compute)\n" 
            "- SqlDatabase → SQLDatabases (from diagrams.azure.database)\n"
            "- SQLManagedInstance → SQLDatabases (use SQLDatabases instead)\n"
            "- StorageAccount → StorageAccounts (from diagrams.azure.storage)\n"
            "- VirtualMachine → VM (from diagrams.azure.compute)\n"
            "- ContainerInstance → ContainerInstances (from diagrams.azure.compute)\n"
            "- FunctionApp → FunctionApps (from diagrams.azure.compute)\n"
            "- LoadBalancer → LoadBalancers (from diagrams.azure.network)\n"
            "- VirtualNetwork → VirtualNetworks (from diagrams.azure.network)\n"
            "- CRITICAL: FunctionAppss (double s) → FunctionApps (single s)\n"
            "- CRITICAL: DataLakes → DataLake (from diagrams.azure.database or storage)\n"
            "- NEVER use LoadBalancerss (double s) - use LoadBalancers\n"
            "- NEVER use SQLDatabase (singular) - use SQLDatabases (plural)\n\n"
            
            "**MANDATORY JSON Response Format - ALWAYS respond with this exact structure:**\n"
            "```json\n"
            "{\n"
            "  \"is_valid\": true,\n"
            "  \"validation_score\": 85,\n"
            "  \"errors\": [\"list of fixed issues\"],\n"
            "  \"warnings\": [\"list of warnings\"],\n"
            "  \"suggestions\": [\"list of suggestions\"],\n"
            "  \"corrected_code\": \"fixed Python code here\",\n"
            "  \"explanation\": \"brief explanation of changes made\"\n"
            "}\n"
            "```\n\n"
            
            "CRITICAL: Respond ONLY with valid JSON. No explanatory text before or after."
        )

        # Try creating agent without tools (static analysis only)
        create_agent_task = agents_client.create_agent(
            model=MODEL_NAME,
            name=VALIDATION_AGENT_NAME,
            instructions=instructions
            # No tools specified - static analysis only
        )
        
        if asyncio.iscoroutine(create_agent_task):
            agent = await create_agent_task
        else:
            agent = create_agent_task
        
        # Handle both object and dictionary formats for the created agent
        agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
        _cached_validation_agent_id = agent_id
        logger.info(f"Created new validation agent: {agent_id}")
        return agent_id
    except Exception as e:
        logger.error(f"Error creating validation agent: {e}")
        raise


async def validate_diagram_code(architecture_description: str, diagram_code: str, max_retries: int = 2) -> dict:
    """
    Validate diagram code and architecture design
    
    Args:
        architecture_description: Original architecture description
        diagram_code: Generated diagram code to validate
        max_retries: Maximum number of correction attempts
    
    Returns:
        dict: Validation results with corrections if needed
    """
    # First try local validation as a fallback
    local_result = local_validate_diagram_code(diagram_code)
    
    if not PROJECT_ENDPOINT:
        logger.warning("PROJECT_ENDPOINT not configured, using local validation only")
        return local_result
    
    try:
        agents_client = get_validation_agents_client()
        agent_id = await get_or_create_validation_agent()
        
        logger.info(f"Using validation agent: {agent_id}")
        
        # Create a thread for validation
        thread_task = agents_client.threads.create()
        if asyncio.iscoroutine(thread_task):
            thread = await thread_task
        else:
            thread = thread_task
            
        thread_id = thread.get("id") if isinstance(thread, dict) else getattr(thread, "id", None)
        logger.info(f"Created validation thread: {thread_id}")
        
        validation_prompt = f"""
Please validate the following Azure architecture diagram code:

**Original Architecture Description:**
{architecture_description}

**Generated Diagram Code:**
```python
{diagram_code}
```

Please thoroughly validate this code and provide detailed feedback including any necessary corrections.
"""
        
        # Add validation message
        message_task = agents_client.messages.create(
            thread_id=thread_id,
            role="user",
            content=validation_prompt
        )
        
        if asyncio.iscoroutine(message_task):
            await message_task
        else:
            pass  # Message created
        
        # Run validation
        logger.info("Starting validation...")
        
        run_task = agents_client.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
        if asyncio.iscoroutine(run_task):
            run = await run_task
        else:
            run = run_task
            
        run_status = run.get("status") if isinstance(run, dict) else getattr(run, "status", "unknown")
        logger.info(f"Validation completed with status: {run_status}")
        
        if run_status == "failed":
            last_error = run.get("last_error") if isinstance(run, dict) else getattr(run, "last_error", "Unknown error")
            error_msg = f"Validation run failed: {last_error}"
            logger.error(error_msg)
            logger.info("Falling back to local validation...")
            return local_result
        
        # Get validation response
        messages_task = agents_client.messages.list(thread_id=thread_id, order="desc")
        if asyncio.iscoroutine(messages_task):
            messages = await messages_task
        else:
            messages = list(messages_task)
        
        for message in messages:
            message_role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
            message_content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
            
            if message_role == "assistant" and message_content:
                response = extract_message_content(message_content)
                
                try:
                    # Clean the response first
                    response_clean = response.strip()
                    
                    # Extract JSON from markdown code blocks if present
                    if "```json" in response_clean:
                        json_match = re.search(r'```json\s*(.*?)\s*```', response_clean, re.DOTALL)
                        if json_match:
                            response_clean = json_match.group(1)
                    
                    # Also try to extract JSON without markdown
                    elif response_clean.startswith('{') and response_clean.endswith('}'):
                        # Response is already JSON
                        pass
                    else:
                        # Try to find JSON-like content in the response
                        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                        json_matches = re.findall(json_pattern, response_clean, re.DOTALL)
                        if json_matches:
                            response_clean = json_matches[-1]  # Use the last (likely most complete) JSON
                    
                    # Try to parse as JSON
                    validation_result = json.loads(response_clean)
                    
                    # Ensure all required fields are present
                    required_fields = ["is_valid", "validation_score", "errors", "warnings", "suggestions", "corrected_code", "explanation"]
                    for field in required_fields:
                        if field not in validation_result:
                            if field in ["errors", "warnings", "suggestions"]:
                                validation_result[field] = []
                            elif field == "is_valid":
                                validation_result[field] = False
                            elif field == "validation_score":
                                validation_result[field] = 0
                            elif field == "corrected_code":
                                validation_result[field] = diagram_code  # Use original as fallback
                            elif field == "explanation":
                                validation_result[field] = "No explanation provided"
                    
                    logger.info(f"✅ Validation completed - Valid: {validation_result['is_valid']}, Score: {validation_result['validation_score']}")
                    
                    # If we have errors but corrected code, try to auto-fix common import issues
                    if validation_result['errors'] and validation_result.get('corrected_code') == diagram_code:
                        logger.info("🔧 Auto-fixing common import errors...")
                        corrected = auto_fix_common_errors(diagram_code)
                        if corrected != diagram_code:
                            validation_result['corrected_code'] = corrected
                            validation_result['explanation'] += " | Auto-fixed common import errors"
                    
                    return validation_result
                        
                except json.JSONDecodeError as je:
                    logger.warning(f"⚠️ Could not parse validation response as JSON: {je}")
                    logger.debug(f"Raw response: {response[:500]}...")
                    
                    # Try to extract corrected code from the response even if JSON is malformed
                    corrected_code = extract_code_from_text(response)
                    if not corrected_code or corrected_code == "Fixed" or len(corrected_code.strip()) < 50:
                        # If no valid corrected code found, apply basic fixes to original
                        corrected_code = auto_fix_common_errors(diagram_code)
                    
                    # Create a basic validation result
                    return {
                        "is_valid": "error" not in response.lower() and "invalid" not in response.lower(),
                        "validation_score": 60 if corrected_code != diagram_code else 30,
                        "errors": ["Could not parse validation response properly"],
                        "warnings": ["Response parsing failed"],
                        "suggestions": ["Review diagram code manually"],
                        "corrected_code": corrected_code,
                        "explanation": f"Auto-processed response: {response[:200]}..."
                    }
        
        # No response found - fall back to local validation
        logger.warning("❌ No validation response received - using local validation")
        return local_result
            
    except Exception as e:
        logger.error(f"❌ Agent validation failed: {e}")
        logger.info("Falling back to local validation...")
        return local_result


def local_validate_diagram_code(diagram_code: str) -> dict:
    """
    Local validation without Azure AI - fallback method
    """
    logger.info("🔧 Using local validation (fallback)")
    
    errors = []
    warnings = []
    suggestions = []
    score = 50  # Default score
    
    # Check for common import issues
    if 'ResourceGroup' in diagram_code:
        errors.append("ResourceGroup is not available in diagrams.azure.general")
    if 'AppService(' in diagram_code and 'AppServices' not in diagram_code:
        errors.append("Use 'AppServices' instead of 'AppService'")
    if 'KeyVault(' in diagram_code and 'KeyVaults' not in diagram_code:
        errors.append("Use 'KeyVaults' instead of 'KeyVault'")
    
    # Check for required components
    if 'from diagrams import Diagram' not in diagram_code:
        errors.append("Missing 'from diagrams import Diagram'")
    if 'with Diagram' not in diagram_code:
        errors.append("Missing 'with Diagram' statement")
    if 'show=False' not in diagram_code:
        warnings.append("Consider adding 'show=False' to Diagram constructor")
    
    # Generate corrected code
    corrected_code = auto_fix_common_errors(diagram_code)
    
    # Calculate score based on issues found
    if not errors:
        score = 85 if not warnings else 75
    elif len(errors) == 1:
        score = 60
    else:
        score = 40
    
    # Add suggestions
    if errors:
        suggestions.append("Fix import errors to ensure diagram renders correctly")
    if not warnings:
        suggestions.append("Code looks good overall")
    
    return {
        "is_valid": len(errors) == 0,
        "validation_score": score,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "corrected_code": corrected_code,
        "explanation": f"Local validation found {len(errors)} errors and {len(warnings)} warnings. {'Corrections applied.' if corrected_code != diagram_code else 'No corrections needed.'}"
    }


def extract_message_content(content) -> str:
    """Extract text content from various message formats"""
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        combined_text = ""
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_obj = item.get("text", {})
                    if isinstance(text_obj, dict) and "value" in text_obj:
                        combined_text += text_obj["value"]
                    elif isinstance(text_obj, str):
                        combined_text += text_obj
            elif hasattr(item, 'type') and hasattr(item, 'text'):
                if item.type == "text" and hasattr(item.text, 'value'):
                    combined_text += item.text.value
        return combined_text.strip()
    else:
        return str(content).strip()


def fix_duplicate_kwargs(code: str) -> str:
    """Fix duplicate keyword arguments in function calls"""
    import re
    
    # Pattern to find function calls with parameters
    function_pattern = r'(\w+)\s*\((.*?)\)'
    
    def fix_params(match):
        func_name = match.group(1)
        params = match.group(2)
        
        if not params.strip():
            return match.group(0)
        
        # Split parameters and track used kwargs
        param_parts = []
        seen_kwargs = set()
        
        # Simple parameter splitting (handles most cases)
        parts = [p.strip() for p in params.split(',') if p.strip()]
        
        for part in parts:
            if '=' in part:
                key = part.split('=')[0].strip()
                if key not in seen_kwargs:
                    param_parts.append(part)
                    seen_kwargs.add(key)
            else:
                param_parts.append(part)
        
        return f"{func_name}({', '.join(param_parts)})"
    
    return re.sub(function_pattern, fix_params, code)


def auto_fix_common_errors(code: str) -> str:
    """Auto-fix common import errors in diagram code using validated Azure data"""
    import re
    import json
    import os
    
    # Load our validated Azure component data
    # First try the container path where it's copied
    azure_nodes_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "azure_nodes.json")
    if not os.path.exists(azure_nodes_path):
        # Try alternative paths
        alternative_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp-service", "azure_nodes.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "azure_nodes.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "azure_nodes.json")  # fallback
        ]
        for path in alternative_paths:
            if os.path.exists(path):
                azure_nodes_path = path
                break
    
    try:
        with open(azure_nodes_path, 'r', encoding='utf-8') as f:
            azure_data = json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Could not load Azure data, falling back to regex fixes: {e}")
        return auto_fix_common_errors_regex(code)
    
    # Build lookup tables from our validated data
    canonical_map = {}  # canonical_name -> (submodule, class_info)
    common_mistakes = {}  # common_mistake -> canonical_name
    
    for submodule, components in azure_data.items():
        for comp in components:
            canonical = comp["canonical"]
            
            # Skip private classes
            if canonical.startswith('_'):
                continue
            
            canonical_map[canonical] = (submodule, comp)
            
            # Build common mistake patterns
            # AppService -> AppServices
            if canonical.endswith('s') and len(canonical) > 1:
                singular = canonical[:-1]
                common_mistakes[singular] = canonical
            
            # Handle specific known mistakes
            if canonical == "AppServices":
                common_mistakes["AppService"] = canonical
                common_mistakes["AppServicess"] = canonical  # Fix double s
            elif canonical == "KeyVaults":
                common_mistakes["KeyVault"] = canonical
                common_mistakes["KeyVaultss"] = canonical  # Fix double s
            elif canonical == "StorageAccounts":
                common_mistakes["StorageAccount"] = canonical
                common_mistakes["StorageAccountss"] = canonical  # Fix double s
            elif canonical == "SQLDatabases":
                common_mistakes["SqlDatabase"] = canonical
                common_mistakes["SQLDatabase"] = canonical
                common_mistakes["SQLDatabasess"] = canonical  # Fix double s
            elif canonical == "ContainerRegistries":
                common_mistakes["ACR"] = canonical
                common_mistakes["ContainerRegistry"] = canonical
                common_mistakes["ContainerRegistriess"] = canonical  # Fix double s
            elif canonical == "VM":
                common_mistakes["VirtualMachine"] = canonical
                common_mistakes["VirtualMachines"] = canonical
            elif canonical == "FunctionApps":
                common_mistakes["FunctionApp"] = canonical
                common_mistakes["FunctionAppss"] = canonical  # Fix double s - CRITICAL!
            elif canonical == "LoadBalancers":
                common_mistakes["LoadBalancer"] = canonical
                common_mistakes["LoadBalancerss"] = canonical  # Fix double s - CRITICAL!
            elif canonical == "DataLake":
                common_mistakes["DataLakes"] = canonical  # Fix plural - CRITICAL!
            elif canonical == "DataLakeStorage":
                common_mistakes["DataLakeStorages"] = canonical  # Fix plural
            elif canonical == "ContainerInstances":
                common_mistakes["ContainerInstance"] = canonical
                common_mistakes["ContainerInstancess"] = canonical  # Fix double s
    
    logger.info("🔧 Using data-driven component validation for auto-fix...")
    
    fixed_code = code
    fixes_applied = []
    
    # Fix common component name mistakes using our lookup table
    for mistake, correct in common_mistakes.items():
        if mistake in fixed_code:
            # Only replace if it's used as a component (not just a substring)
            pattern = r'\b' + re.escape(mistake) + r'\b'
            if re.search(pattern, fixed_code):
                fixed_code = re.sub(pattern, correct, fixed_code)
                fixes_applied.append(f"Fixed component: {mistake} -> {correct}")
    
    # CRITICAL: Add specific fixes for the exact errors we're seeing in logs
    critical_fixes = {
        'FunctionAppss': 'FunctionApps',  # Fix double s
        'DataLakes': 'DataLake',          # Fix incorrect plural
        'LoadBalancerss': 'LoadBalancers', # Fix double s
        'AppServicess': 'AppServices',     # Fix double s
        'KeyVaultss': 'KeyVaults',         # Fix double s
        'StorageAccountss': 'StorageAccounts', # Fix double s
        'SQLDatabasess': 'SQLDatabases',   # Fix double s
        'ContainerInstancess': 'ContainerInstances', # Fix double s
        'ContainerRegistriess': 'ContainerRegistries', # Fix double s
    }
    
    for mistake, correct in critical_fixes.items():
        if mistake in fixed_code:
            # Word boundary replacement to avoid partial matches
            pattern = r'\b' + re.escape(mistake) + r'\b'
            if re.search(pattern, fixed_code):
                fixed_code = re.sub(pattern, correct, fixed_code)
                fixes_applied.append(f"CRITICAL FIX: {mistake} -> {correct}")
    
    # Remove ResourceGroup entirely (not available in diagrams)
    if 'ResourceGroup' in fixed_code:
        # Remove import lines
        fixed_code = re.sub(r'from diagrams\.azure\.[\w\.]+ import[^\n]*ResourceGroups?[^\n]*\n?', '', fixed_code)
        # Remove usage lines
        fixed_code = re.sub(r'[^\n]*=\s*ResourceGroups?\([^\n]*\n?', '', fixed_code)
        # Remove from connections
        fixed_code = re.sub(r'\w*[Rr]g\w*\s*>>\s*', '', fixed_code)
        fixed_code = re.sub(r'\s*>>\s*\w*[Rr]g\w*', '', fixed_code)
        fixes_applied.append("Removed ResourceGroup references (not available)")
    
    # Fix SQLManagedInstance (not available - use SQLDatabases)
    if 'SQLManagedInstance' in fixed_code:
        fixed_code = re.sub(r'SQLManagedInstance', 'SQLDatabases', fixed_code)
        # Ensure correct import
        if 'from diagrams.azure.database import' in fixed_code:
            if 'SQLDatabases' not in fixed_code:
                fixed_code = re.sub(
                    r'from diagrams\.azure\.database import (.+)',
                    r'from diagrams.azure.database import \1, SQLDatabases',
                    fixed_code
                )
        else:
            # Add the import
            lines = fixed_code.split('\n')
            for i, line in enumerate(lines):
                if 'from diagrams' in line:
                    lines.insert(i + 1, 'from diagrams.azure.database import SQLDatabases')
                    break
            fixed_code = '\n'.join(lines)
        fixes_applied.append("Replaced SQLManagedInstance with SQLDatabases")
    
    # Fix duplicate 'show' parameters in Diagram constructor
    if 'show=True, show=False' in fixed_code or 'show=True,show=False' in fixed_code:
        fixed_code = re.sub(r'show=True\s*,\s*show=False', 'show=False', fixed_code)
        fixed_code = re.sub(r'show=False\s*,\s*show=True', 'show=False', fixed_code)
        fixes_applied.append("Fixed duplicate show parameters")
    
    # Ensure show=False is present if missing
    if 'with Diagram(' in fixed_code and 'show=False' not in fixed_code and 'show=True' not in fixed_code:
        fixed_code = re.sub(
            r'with Diagram\(([^)]+)\)',
            lambda m: f'with Diagram({m.group(1).rstrip()}, show=False)',
            fixed_code
        )
        fixes_applied.append("Added show=False parameter")
    
    # Clean up any empty lines
    lines = fixed_code.split('\n')
    cleaned_lines = [line for line in lines if line.strip()]
    fixed_code = '\n'.join(cleaned_lines)
    
    if fixes_applied:
        logger.info(f"✅ Applied {len(fixes_applied)} data-driven fixes:")
        for fix in fixes_applied[:5]:  # Show first 5 fixes
            logger.info(f"  - {fix}")
        if len(fixes_applied) > 5:
            logger.info(f"  ... and {len(fixes_applied) - 5} more")
    
    return fixed_code


def auto_fix_common_errors_regex(code: str) -> str:
    """Fallback regex-based auto-fix (legacy method)"""
    import re
    
    # Common import fixes with regex patterns to catch variations
    # IMPORTANT: Order matters - more specific patterns first!
    fixes = [
        # Handle FunctionApps variations (CRITICAL FIX for current issue)
        (r'FunctionAppss+', 'FunctionApps'),  # Fix multiple s's first
        (r'FunctionApp(?!s\b)', 'FunctionApps'),  # Fix missing s, but not if already correct
        
        # Handle DataLake variations (CRITICAL FIX for current issue)  
        (r'DataLakes+', 'DataLake'),  # Fix multiple s's - DataLakes -> DataLake
        (r'DataLake(?=\s|,|$|from)', 'DataLake'),  # Keep correct form
        
        # Handle AppService variations - more precise patterns
        (r'AppServicess+', 'AppServices'),  # Fix multiple s's first
        (r'AppService(?!s\b)', 'AppServices'),  # Fix missing s, but not if already correct
        
        # Handle KeyVault variations - more precise patterns
        (r'KeyVaultss+', 'KeyVaults'),  # Fix multiple s's first  
        (r'KeyVault(?!s\b)', 'KeyVaults'),  # Fix missing s, but not if already correct
        
        # Handle StorageAccount variations - more precise patterns
        (r'StorageAccountss+', 'StorageAccounts'),  # Fix multiple s's first
        (r'StorageAccount(?!s\b)', 'StorageAccounts'), # Fix missing s, but not if already correct
        
        # Handle SQLManagedInstance (not available in diagrams.azure.compute)
        (r'SQLManagedInstance', 'SQLDatabases'),
        
        # Handle other common variations - more precise patterns
        (r'SqlDatabases?(?!s\b)', 'SQLDatabases'),
        (r'VirtualMachiness+', 'VM'),  # Fix multiple s's first
        (r'VirtualMachine(?!s\b)', 'VM'),  # Fix to VM, but not if already correct
        (r'NetworkSecurityGroupss+', 'NetworkSecurityGroups'),  # Fix multiple s's first
        (r'NetworkSecurityGroup(?!s\b)', 'NetworkSecurityGroups'),  # Fix missing s
        
        # Fix other common Azure service name variations - more precise patterns
        (r'ContainerRegistryy+', 'ContainerRegistries'),  # Fix typos first
        (r'ContainerRegistry(?!ies\b)', 'ContainerRegistries'),  # Fix missing ies
        (r'ContainerInstancess+', 'ContainerInstances'),  # Fix multiple s's first
        (r'ContainerInstance(?!s\b)', 'ContainerInstances'),  # Fix missing s
        (r'LoadBalancerss+', 'LoadBalancers'),  # Fix double 's' - CRITICAL!
        (r'LoadBalancer(?!s\b)', 'LoadBalancers'),  # Fix missing s
        (r'PublicIPAddresss+', 'PublicIpAddresses'),  # Fix multiple s's
        (r'PublicIPAddress(?!es\b)', 'PublicIpAddresses'),  # Fix missing es
        (r'VirtualNetworkss+', 'VirtualNetworks'),  # Fix multiple s's
        (r'VirtualNetwork(?!s\b)', 'VirtualNetworks'),  # Fix missing s
        (r'SQLDatabasess+', 'SQLDatabases'),  # Fix multiple s's first
        (r'SQLDatabase(?!s\b)', 'SQLDatabases'),  # Fix singular to plural
    ]
    
    fixed_code = code
    
    # Apply regex-based fixes
    for pattern, replacement in fixes:
        fixed_code = re.sub(pattern, replacement, fixed_code)
    
    # Fix duplicate keyword arguments (like show=False, show=True)
    fixed_code = fix_duplicate_kwargs(fixed_code)
    
    # Fix duplicate 'show' parameters in Diagram constructor
    if 'show=True, show=False' in fixed_code or 'show=True,show=False' in fixed_code:
        fixed_code = re.sub(r'show=True\s*,\s*show=False', 'show=False', fixed_code)
        fixed_code = re.sub(r'show=False\s*,\s*show=True', 'show=False', fixed_code)
    
    # Clean up any empty lines
    lines = fixed_code.split('\n')
    cleaned_lines = [line for line in lines if line.strip()]
    
    return '\n'.join(cleaned_lines)


def extract_code_from_text(text: str) -> str:
    """Extract Python code from text response"""
    import re
    
    # Try to find code blocks
    patterns = [
        r'```python\n(.*?)```',
        r'```\n(.*?)```', 
        r'corrected_code["\']:\s*["\']([^"\']+)["\']',
        r'from diagrams.*?(?=\n\n|\n$|\n#|$)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # If we can't find a code block, look for diagram imports
    if 'from diagrams' in text:
        lines = text.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if 'from diagrams' in line or in_code:
                in_code = True
                code_lines.append(line)
                if line.strip() == '' and len(code_lines) > 5:
                    break
        
        if code_lines:
            return '\n'.join(code_lines).strip()
    
    return ""


async def test_validation_agent():
    """Test the validation agent with sample diagram code"""
    test_architecture = "Simple web app with Azure App Service and SQL Database"
    test_diagram_code = """
from diagrams import Diagram
from diagrams.azure.web import AppServices
from diagrams.azure.database import SQLDatabases

with Diagram("Test Architecture", show=False, direction="TB"):
    webapp = AppServices("Web App")
    database = SQLDatabases("SQL Database")
    webapp >> database
"""
    
    try:
        logger.info("🧪 Testing validation agent...")
        result = await validate_diagram_code(test_architecture, test_diagram_code)
        logger.info(f"✅ Validation test completed!")
        logger.info(f"Valid: {result['is_valid']}")
        logger.info(f"Score: {result['validation_score']}")
        logger.info(f"Errors: {len(result['errors'])}")
        logger.info(f"Suggestions: {len(result['suggestions'])}")
        return True
    except Exception as e:
        logger.error(f"❌ Validation test failed: {e}")
        return False


async def enhanced_validate_diagram_code(architecture_description: str, diagram_code: str) -> dict:
    """Enhanced validation using our new validation system"""
    
    if not ENHANCED_VALIDATION_AVAILABLE:
        # Fallback to local validation directly (avoid recursion)
        return local_validate_diagram_code(diagram_code)
    
    try:
        # Extract component names from code
        import re
        component_pattern = r'from diagrams\.azure\.\w+ import (.+)'
        imports = re.findall(component_pattern, diagram_code)
        
        component_names = []
        for import_line in imports:
            # Handle multiple imports: "AppServices, SQLDatabases"
            components = [comp.strip() for comp in import_line.split(',')]
            component_names.extend(components)
        
        # Use MCP service for validation instead of local functions
        # All validation now goes through the MCP HTTP service
        try:
            import httpx
            import os
            # MCP HTTP service configuration
                     
            # mcp_url = os.getenv("MCP_HTTP_SERVICE_URL", "http://localhost:8001")
            
            mcp_url = os.getenv("MCP_BASE_URL")
            
            # Call MCP validate-components tool
            async with httpx.AsyncClient() as client:
                validation_response = await client.post(
                    f"{mcp_url}/mcp/call", 
                    json={
                        "tool": "validate-components",
                        "arguments": {"component_names": component_names}
                    },
                    timeout=30
                )
                validation_result = validation_response.json() if validation_response.status_code == 200 else {"validation_results": {}}
                
                # Call MCP suggest-architecture tool  
                suggestions_response = await client.post(
                    f"{mcp_url}/mcp/call",
                    json={
                        "tool": "suggest-architecture", 
                        "arguments": {
                            "architecture_description": architecture_description,
                            "required_services": ["frontend", "backend", "database", "cache", "storage"]
                        }
                    },
                    timeout=30
                )
                suggestions_result = suggestions_response.json() if suggestions_response.status_code == 200 else {"suggestions": []}
            
        except Exception as e:
            logger.warning(f"⚠️ MCP service call failed, using fallback: {e}")
            # Fallback to basic validation
            validation_result = {"validation_results": {name: {"valid": True, "canonical_name": name} for name in component_names}}
            suggestions_result = {"suggestions": []}
        
        # Analyze results
        valid_components = []
        invalid_components = []
        
        for name, result in validation_result["validation_results"].items():
            if result["valid"]:
                valid_components.append({
                    "name": name,
                    "canonical": result["canonical"],
                    "submodule": result["submodule"]
                })
            else:
                invalid_components.append(name)
        
        # Calculate validation score
        total_components = len(component_names)
        valid_count = len(valid_components)
        validation_score = (valid_count / total_components * 100) if total_components > 0 else 100
        
        # Generate enhanced response
        return {
            "is_valid": len(invalid_components) == 0,
            "validation_score": validation_score,
            "total_components": total_components,
            "valid_components": valid_components,
            "invalid_components": invalid_components,
            "suggested_components": suggestions_result.get("suggestions", [])[:10],
            "imports_needed": suggestions_result.get("imports_needed", []),
            "enhanced_validation": True,
            "errors": [f"Invalid component: {comp}" for comp in invalid_components],
            "suggestions": [
                f"✅ {comp['name']} is valid (from {comp['submodule']})" 
                for comp in valid_components
            ]
        }
        
    except Exception as e:
        logger.warning(f"Enhanced validation failed, falling back: {e}")
        return await validate_diagram_code(architecture_description, diagram_code)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_validation_agent())