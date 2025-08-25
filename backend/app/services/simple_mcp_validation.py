"""
Simple MCP-only validation - Single source of truth
"""
import httpx
import json
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# MCP service configuration - Use DAPR for internal communication
DAPR_PORT = "3500"
DAPR_SERVICE_ID = "mcp-service"
MCP_SERVICE_URL = f"http://localhost:{DAPR_PORT}/v1.0/invoke/{DAPR_SERVICE_ID}/method"
MCP_TIMEOUT = 30

async def extract_components_from_code(diagram_code: str) -> List[str]:
    """Extract Azure component names from import statements"""
    components = []
    import_pattern = r'from diagrams\.azure\.\w+ import ([\w, ]+)'
    
    matches = re.findall(import_pattern, diagram_code)
    for imports in matches:
        # Split multiple imports and clean them
        comps = [comp.strip().split(' as ')[0] for comp in imports.split(',')]
        components.extend([comp.strip() for comp in comps])
    
    return list(set(components))  # Remove duplicates

async def validate_and_fix_diagram_code_simple(diagram_code: str, architecture_description: str = "") -> Dict[str, Any]:
    """
    Simple MCP-only validation and fixing - Single source of truth
    
    Returns:
        dict: Contains is_valid, corrected_code, errors, etc.
    """
    try:
        logger.info("🔌 Using MCP service as single source of truth for validation...")
        
        # Step 1: Extract all Azure components from the code
        components = await extract_components_from_code(diagram_code)
        if not components:
            logger.warning("No Azure components found in code")
            return {
                "is_valid": True,
                "validation_score": 80,
                "corrected_code": diagram_code,
                "errors": [],
                "warnings": ["No Azure components detected"],
                "suggestions": [],
                "explanation": "No Azure components to validate"
            }
        
        logger.info(f"� Found components to validate: {components}")
        
        # Step 2: Validate components via MCP
        async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_SERVICE_URL}/mcp/tools/call",
                json={
                    "name": "validate_azure_components",
                    "arguments": {
                        "component_names": components
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"❌ MCP component validation failed: {response.status_code}")
                return {
                    "is_valid": False,
                    "validation_score": 0,
                    "corrected_code": diagram_code,
                    "errors": [f"MCP service error: {response.status_code}"],
                    "warnings": [],
                    "suggestions": ["Check MCP service connectivity"],
                    "explanation": "MCP validation service unavailable"
                }
            
            result = response.json()
            if not result.get("success") or result.get("error"):
                logger.error(f"❌ MCP validation failed: {result}")
                return {
                    "is_valid": False,
                    "validation_score": 0,
                    "corrected_code": diagram_code,
                    "errors": ["MCP validation failed"],
                    "warnings": [],
                    "suggestions": ["Check MCP service response"],
                    "explanation": "MCP validation error"
                }
            
            # Parse MCP validation result
            mcp_result = result["result"]["result"]
            if mcp_result.get("isError"):
                logger.error(f"❌ MCP returned error: {mcp_result}")
                return {
                    "is_valid": False,
                    "validation_score": 0,
                    "corrected_code": diagram_code,
                    "errors": ["MCP validation error"],
                    "warnings": [],
                    "suggestions": [],
                    "explanation": "MCP validation failed"
                }
            
            # Parse the validation results
            validation_content = mcp_result["content"][0]["text"]
            validation_data = json.loads(validation_content)
            
            logger.info(f"✅ MCP validation successful: {validation_data}")
            
            # Step 3: Apply fixes based on MCP results
            corrected_code = diagram_code
            errors = []
            corrections_made = []
            
            validation_results = validation_data.get("validation_results", {})
            
            for component, result_data in validation_results.items():
                if result_data.get("valid"):
                    correct_import = result_data.get("import_path")
                    canonical_name = result_data.get("canonical")
                    
                    # Fix import path if needed
                    if correct_import:
                        # Replace incorrect import with correct one
                        import_pattern = rf'from diagrams\.azure\.\w+ import ([^,\n]*{re.escape(component)}[^,\n]*)'
                        corrected_import = f'from {correct_import} import {canonical_name}'
                        
                        if re.search(import_pattern, corrected_code):
                            corrected_code = re.sub(
                                rf'from diagrams\.azure\.\w+ import ([^,\n]*{re.escape(component)}[^,\n]*)',
                                corrected_import,
                                corrected_code
                            )
                            corrections_made.append(f"Fixed import for {component}: {corrected_import}")
                        
                        # Fix class name if different from original
                        if canonical_name != component:
                            corrected_code = re.sub(
                                rf'\b{re.escape(component)}\b',
                                canonical_name,
                                corrected_code
                            )
                            corrections_made.append(f"Fixed class name: {component} → {canonical_name}")
                else:
                    # Handle invalid components with suggestions
                    suggestions = result_data.get("suggestions", [])
                    if suggestions:
                        # Use the first suggestion (most relevant)
                        best_suggestion = suggestions[0]
                        suggested_name = best_suggestion["name"]
                        suggested_submodule = best_suggestion["submodule"]
                        suggested_import = f"diagrams.azure.{suggested_submodule}"
                        
                        # Replace the invalid component with the suggested one
                        # Fix import
                        import_pattern = rf'from diagrams\.azure\.\w+ import ([^,\n]*{re.escape(component)}[^,\n]*)'
                        corrected_import = f'from {suggested_import} import {suggested_name}'
                        
                        if re.search(import_pattern, corrected_code):
                            corrected_code = re.sub(import_pattern, corrected_import, corrected_code)
                            corrections_made.append(f"Fixed invalid component {component} → {suggested_name}: {corrected_import}")
                        
                        # Fix class usage in code
                        corrected_code = re.sub(
                            rf'\b{re.escape(component)}\b',
                            suggested_name,
                            corrected_code
                        )
                        corrections_made.append(f"Replaced {component} with {suggested_name} in code")
                    else:
                        errors.append(f"Component '{component}' is not valid in Azure diagrams and no suggestions available")
            
            # Check if we have invalid components
            invalid_count = validation_data.get("invalid_count", 0)
            valid_count = validation_data.get("valid_count", 0)
            
            is_valid = invalid_count == 0
            validation_score = int((valid_count / len(components)) * 100) if components else 100
            
            explanation = f"MCP validation completed: {valid_count} valid, {invalid_count} invalid components"
            if corrections_made:
                explanation += f". Applied fixes: {', '.join(corrections_made)}"
            
            return {
                "is_valid": is_valid,
                "validation_score": validation_score,
                "corrected_code": corrected_code,
                "errors": errors,
                "warnings": [],
                "suggestions": corrections_made,
                "explanation": explanation
            }
            
    except Exception as e:
        logger.error(f"❌ MCP validation error: {e}")
        return {
            "is_valid": False,
            "validation_score": 0,
            "corrected_code": diagram_code,
            "errors": [f"MCP service error: {str(e)}"],
            "warnings": [],
            "suggestions": ["Check MCP service connectivity"],
            "explanation": f"MCP validation failed: {str(e)}"
        }
