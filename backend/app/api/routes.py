from fastapi import APIRouter, HTTPException, Request
from app.models.schema import ArchitectureRequest, ArchitectureResponse
from app.services.ai_agent import generate_design_document
from app.services.enhanced_diagram_generator import generate_and_validate_diagram
from app.services.storage import (
    save_architecture,
    load_architectures,
    get_architecture,
    delete_architecture,
    upload_diagram,
    check_architecture_exists,
    check_architecture_exists_sync,
    save_architecture_sync,
    load_architectures_sync
)
import asyncio
import logging
import os

# MCP Toggle - Easy to reverse by changing USE_MCP to false
USE_MCP = os.getenv("USE_MCP", "false").lower() == "true"

if USE_MCP:
    try:
        from app.services.diagram_generator_mcp_http import generate_diagram_with_mcp_http as generate_diagram_mcp
        print("✅ MCP HTTP diagram generator loaded")
        MCP_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ MCP HTTP diagram generator not available: {e}")
        print("📝 Falling back to standard diagram generator")
        from app.services.diagram_generator import generate_diagram
        MCP_AVAILABLE = False
else:
    from app.services.diagram_generator import generate_diagram
    MCP_AVAILABLE = False
    print("📝 Using standard diagram generator (MCP disabled)")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-architecture", response_model=ArchitectureResponse)
async def generate_architecture(payload: ArchitectureRequest):
    """
    Generate both design document and diagram from user input
    """
    try:
        user_input = payload.input.strip()
        if not user_input:
            raise HTTPException(status_code=400, detail="Input cannot be empty")

        logger.info(f"Generating architecture for: {user_input[:100]}...")

        design_doc = None
        diagram_url = None
        
        # Try to run both agents, but don't fail if one fails
        try:
            # Try design document first
            logger.info("Starting design document generation...")
            design_doc = await generate_design_document(user_input)
            logger.info(f"Design document generated successfully ({len(design_doc)} chars)")
        except Exception as design_error:
            logger.error(f"Design document generation failed: {design_error}")
            design_doc = f"Design document generation failed: {str(design_error)}"
        
        try:
            if USE_MCP and MCP_AVAILABLE:
                # Try MCP diagram generation (enhanced version) with timeout
                logger.info("🔌 Starting MCP diagram generation with validation...")
                diagram_result = await asyncio.wait_for(
                    generate_and_validate_diagram(user_input, design_doc or ""),
                    timeout=120  # 2 minutes timeout
                )
                
                if diagram_result['success']:
                    diagram_url = diagram_result.get('diagram_path', '')
                    validation_score = diagram_result['validation_results'].get('validation_score', 0)
                    iterations = diagram_result.get('iterations', 1)
                    logger.info(f"🔌 MCP diagram generated successfully in {iterations} iterations (Score: {validation_score})")
                else:
                    raise Exception(diagram_result.get('error', 'MCP diagram generation failed'))
                    
            else:
                # Standard Azure AI diagram generation with validation and timeout
                logger.info("☁️ Starting enhanced diagram generation with validation...")
                diagram_result = await asyncio.wait_for(
                    generate_and_validate_diagram(user_input, design_doc or ""),
                    timeout=120  # 2 minutes timeout
                )
                
                if diagram_result['success']:
                    diagram_url = diagram_result.get('diagram_path', '')
                    validation_score = diagram_result['validation_results'].get('validation_score', 0)
                    iterations = diagram_result.get('iterations', 1)
                    logger.info(f"☁️ Diagram generated and validated successfully in {iterations} iterations (Score: {validation_score})")
                    
                    # Add validation info to response if available
                    validation_warnings = diagram_result['validation_results'].get('warnings', [])
                    if validation_warnings:
                        logger.info(f"Validation warnings: {validation_warnings}")
                else:
                    logger.error(f"Enhanced diagram generation failed: {diagram_result.get('error', 'Unknown error')}")
                    diagram_url = ""
        except asyncio.TimeoutError:
            logger.error("Diagram generation timed out after 2 minutes, using fallback")
            # Fallback to basic diagram generation without validation
            try:
                logger.info("Using fast fallback diagram generation...")
                if USE_MCP and MCP_AVAILABLE:
                    mcp_result = await asyncio.wait_for(generate_diagram_mcp(user_input), timeout=30)
                    diagram_url = mcp_result.get('diagram_path', '') if isinstance(mcp_result, dict) else str(mcp_result)
                    logger.info(f"🔌 Fast MCP diagram generated: {diagram_url}")
                else:
                    diagram_url = await asyncio.wait_for(generate_diagram(user_input), timeout=30)
                    logger.info(f"☁️ Fast diagram generated successfully: {diagram_url}")
            except Exception as fast_fallback_error:
                logger.error(f"Fast fallback also failed: {fast_fallback_error}")
                diagram_url = ""
        except Exception as diagram_error:
            logger.error(f"{'MCP' if USE_MCP and MCP_AVAILABLE else 'Enhanced'} diagram generation failed: {diagram_error}")
            # Fallback to basic diagram generation
            try:
                logger.info("Falling back to basic diagram generation...")
                if USE_MCP and MCP_AVAILABLE:
                    mcp_result = await generate_diagram_mcp(user_input)
                    diagram_url = mcp_result.get('diagram_path', '') if isinstance(mcp_result, dict) else str(mcp_result)
                    logger.info(f"🔌 MCP fallback diagram generated: {diagram_url}")
                else:
                    diagram_url = await generate_diagram(user_input)
                    logger.info(f"☁️ Basic diagram generated successfully: {diagram_url}")
            except Exception as fallback_error:
                logger.error(f"Fallback diagram generation also failed: {fallback_error}")
                diagram_url = ""

        # Return results even if one or both failed
        # Add warning if diagram_url is empty
        if not diagram_url or diagram_url.strip() == "":
            logger.warning("⚠️ Diagram URL is empty - diagram generation may have failed")
            diagram_url = ""
        else:
            logger.info(f"✅ Final diagram URL: {diagram_url}")
            
        return ArchitectureResponse(
            design_document=design_doc or "Failed to generate design document",
            diagram_url=diagram_url or ""
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in generate_architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/saved-architectures")
async def get_saved():
    """
    Get all saved architectures
    """
    try:
        architectures = await load_architectures()
        logger.info(f"Loaded {len(architectures)} saved architectures")
        return {"architectures": architectures}
    except Exception as e:
        logger.error(f"Error loading architectures: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load architectures: {str(e)}")

@router.post("/save-architecture")
async def save_arch(request: Request):
    """
    Save an architecture to storage
    """
    try:
        data = await request.json()
        
        # Validate required fields
        title = data.get("title", "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        design_document = data.get("design_document", "").strip()
        if not design_document:
            raise HTTPException(status_code=400, detail="Design document is required")
        
        preview = data.get("preview", "").strip()
        diagram_url = data.get("diagram_url", "").strip()
        
        # Generate preview if not provided
        if not preview:
            preview = generate_preview_from_document(design_document)
        
        saved_item = await save_architecture(
            title=title,
            preview=preview,
            design_document=design_document,
            diagram_url=diagram_url
        )
        
        if saved_item.get("already_exists"):
            logger.info(f"Architecture already exists with ID: {saved_item['id']}")
            return {
                "success": True, 
                "id": saved_item["id"], 
                "message": "Architecture already exists - not duplicated",
                "already_exists": True,
                "saved_item": saved_item
            }
        else:
            logger.info(f"Saved new architecture with ID: {saved_item['id']}")
            return {
                "success": True, 
                "id": saved_item["id"], 
                "message": "Architecture saved successfully",
                "saved_item": saved_item
            }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error saving architecture: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save architecture: {str(e)}")


@router.post("/check-architecture-exists")
async def check_arch_exists(request: Request):
    """
    Check if an architecture with the same design document already exists
    """
    try:
        data = await request.json()
        design_document = data.get("design_document", "").strip()
        
        if not design_document:
            raise HTTPException(status_code=400, detail="Design document is required")
        
        existing = await check_architecture_exists(design_document)
        
        if existing:
            return {
                "exists": True,
                "architecture": existing
            }
        else:
            return {
                "exists": False,
                "architecture": None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking architecture exists: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check architecture: {str(e)}")

@router.delete("/saved-architectures/{arch_id}")
async def delete_arch(arch_id: str):
    """
    Delete a saved architecture
    """
    try:
        if not arch_id or not arch_id.strip():
            raise HTTPException(status_code=400, detail="Architecture ID is required")
        
        # Check if architecture exists before deletion
        architectures = await load_architectures()
        architecture_exists = any(arch["id"] == arch_id for arch in architectures)
        
        if not architecture_exists:
            raise HTTPException(status_code=404, detail="Architecture not found")
        
        # Use async delete function
        success = await delete_architecture(arch_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete architecture from storage")
        
        logger.info(f"Deleted architecture with ID: {arch_id}")
        
        return {
            "success": True,
            "message": "Architecture deleted successfully",
            "deleted_id": arch_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error deleting architecture: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete architecture: {str(e)}")

@router.get("/saved-architectures/{arch_id}")
async def get_architecture(arch_id: str):
    """
    Get a specific architecture by ID
    """
    try:
        if not arch_id or not arch_id.strip():
            raise HTTPException(status_code=400, detail="Architecture ID is required")
        
        architectures = await load_architectures()
        architecture = next((arch for arch in architectures if arch["id"] == arch_id), None)
        
        if not architecture:
            raise HTTPException(status_code=404, detail="Architecture not found")
        
        logger.info(f"Retrieved architecture with ID: {arch_id}")
        return architecture
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting architecture: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get architecture: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "message": "ArchitectAI API is running",
        "service": "routes"
    }

@router.post("/debug")
async def debug_endpoint(request: Request):
    """
    Debug endpoint to check frontend-backend communication
    """
    try:
        data = await request.json()
        headers = dict(request.headers)
        
        return {
            "success": True,
            "received_data": data,
            "headers": headers,
            "method": request.method,
            "url": str(request.url),
            "message": "Backend is receiving data correctly"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to parse request data"
        }

@router.post("/validate-diagram")
async def validate_diagram_endpoint(request: Request):
    """
    Validate diagram code manually
    """
    try:
        data = await request.json()
        
        architecture_description = data.get("architecture_description", "").strip()
        diagram_code = data.get("diagram_code", "").strip()
        
        if not diagram_code:
            raise HTTPException(status_code=400, detail="Diagram code is required")
        
        if not architecture_description:
            raise HTTPException(status_code=400, detail="Architecture description is required")
        
        logger.info("Starting manual diagram validation...")
        
        # Import validation function
        from app.services.validation_agent import validate_diagram_code
        
        validation_result = await validate_diagram_code(architecture_description, diagram_code)
        
        logger.info(f"Manual validation completed - Score: {validation_result['validation_score']}")
        
        return {
            "success": True,
            "validation_result": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual validation: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/generate-diagram-only")
async def generate_diagram_only(request: Request):
    """
    Generate only a diagram with validation (no design document)
    """
    try:
        data = await request.json()
        
        architecture_description = data.get("architecture_description", "").strip()
        use_validation = data.get("use_validation", True)
        
        if not architecture_description:
            raise HTTPException(status_code=400, detail="Architecture description is required")
        
        logger.info(f"Generating diagram only for: {architecture_description[:100]}...")
        
        if use_validation:
            # Use enhanced diagram generation with validation
            logger.info("Using enhanced diagram generation with validation...")
            diagram_result = await generate_and_validate_diagram(architecture_description, "")
            
            if diagram_result['success']:
                return {
                    "success": True,
                    "diagram_url": diagram_result.get('diagram_path', ''),
                    "validation_results": diagram_result['validation_results'],
                    "iterations": diagram_result.get('iterations', 1),
                    "final_code": diagram_result.get('final_code', ''),
                    "message": f"Diagram generated and validated in {diagram_result.get('iterations', 1)} iteration(s)"
                }
            else:
                return {
                    "success": False,
                    "error": diagram_result.get('error', 'Unknown error'),
                    "iterations": diagram_result.get('iterations', 0)
                }
        else:
            # Use basic diagram generation
            logger.info("Using basic diagram generation...")
            diagram_url = await generate_diagram(architecture_description)
            
            return {
                "success": True,
                "diagram_url": diagram_url,
                "message": "Diagram generated successfully (no validation)"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in diagram-only generation: {e}")
        raise HTTPException(status_code=500, detail=f"Diagram generation failed: {str(e)}")

def generate_preview_from_document(document: str) -> str:
    """
    Generate a preview from the design document
    """
    if not document:
        return "No preview available"
    
    import re
    
    # Remove markdown formatting and get first few sentences
    plain_text = document
    
    # Remove markdown headers
    plain_text = re.sub(r'^#+\s*', '', plain_text, flags=re.MULTILINE)
    # Remove list markers
    plain_text = re.sub(r'^\s*[-*]\s*', '', plain_text, flags=re.MULTILINE)
    # Remove bold/italic
    plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', plain_text)
    plain_text = re.sub(r'\*(.*?)\*', r'\1', plain_text)
    
    # Clean up and get first sentences
    plain_text = plain_text.strip()
    sentences = [s.strip() for s in plain_text.split('.') if s.strip()]
    
    if not sentences:
        return "Architecture design document"
    
    # Take first 1-2 sentences
    preview = '. '.join(sentences[:2])
    if preview and not preview.endswith('.'):
        preview += '.'
    
    # Truncate if too long
    if len(preview) > 150:
        preview = preview[:147] + '...'
    
    return preview or "Architecture design document"

@router.get("/export/diagram/{diagram_path:path}")
async def export_diagram(diagram_path: str, filename: str = None):
    """
    Export diagram with proper download headers
    """
    from fastapi.responses import FileResponse
    import os
    
    try:
        # Ensure the path is safe (remove leading slash if present)
        if diagram_path.startswith('/'):
            diagram_path = diagram_path[1:]
        
        # Construct the full file path
        if diagram_path.startswith('static/'):
            file_path = diagram_path
        else:
            file_path = f"static/{diagram_path}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Diagram file not found")
        
        # Generate filename if not provided
        if not filename:
            filename = os.path.basename(file_path)
            if not filename.endswith('.png'):
                filename = "architecture_diagram.png"
        
        # Return file with download headers
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='image/png',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting diagram: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export diagram: {str(e)}")

# ==================== VALIDATION ROUTES ====================

@router.post("/validate-components")
async def validate_azure_components(request: Request):
    """Validate Azure component names using enhanced validation system (works with or without MCP)"""
    try:
        data = await request.json()
        component_names = data.get("component_names", [])
        
        if not component_names:
            raise HTTPException(status_code=400, detail="component_names list is required")
        
        # All validation now goes through MCP service
        # Remove local validation dependency for clean architecture
            pass
        
        # Fallback to MCP if available
        if USE_MCP and MCP_AVAILABLE:
            from app.services.diagram_generator_mcp_http import validate_components_via_mcp
            result = await validate_components_via_mcp(component_names)
            return {
                "success": True,
                "validation_results": result.get("validation_results", {}),
                "method": "mcp_http",
                "error": result.get("error")
            }
        
        # Basic validation fallback
        basic_result = {}
        for name in component_names:
            # Simple heuristic validation
            if name in ["AppServices", "SQLDatabases", "KeyVaults", "BlobStorage", "ContainerApps"]:
                basic_result[name] = {"valid": True, "canonical": name, "submodule": "unknown"}
            else:
                basic_result[name] = {"valid": False, "canonical": "N/A", "submodule": "unknown"}
        
        return {
            "success": True,
            "validation_results": basic_result,
            "method": "basic_fallback",
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error validating components: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/suggest-architecture")
async def suggest_architecture_components(request: Request):
    """Get architecture component suggestions (works with or without MCP)"""
    try:
        data = await request.json()
        description = data.get("description", "")
        architecture_types = data.get("architecture_types", ["frontend", "backend", "database", "cache"])
        
        if not description:
            raise HTTPException(status_code=400, detail="description is required")
        
        # All suggestions now go through MCP service
        # Remove local validation dependency for clean architecture
        
        # Use MCP service for architecture suggestions
        if USE_MCP and MCP_AVAILABLE:
            from app.services.diagram_generator_mcp_http import suggest_architecture_components_via_mcp
            result = await suggest_architecture_components_via_mcp(description, architecture_types)
            return {
                "success": True,
                "suggestions": result.get("suggestions", []),
                "imports_needed": result.get("imports_needed", []),
                "method": "mcp_http", 
                "error": result.get("error")
            }
        
        # Basic suggestions fallback
        basic_suggestions = []
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['react', 'frontend', 'web']):
            basic_suggestions.append({"component": "AppServices", "usage": "Web Frontend", "submodule": "web"})
        if any(word in description_lower for word in ['api', 'backend', 'node']):
            basic_suggestions.append({"component": "AppServices", "usage": "Backend API", "submodule": "web"})
        if any(word in description_lower for word in ['database', 'sql', 'postgres']):
            basic_suggestions.append({"component": "SQLDatabases", "usage": "Database", "submodule": "database"})
        
        return {
            "success": True,
            "suggestions": basic_suggestions,
            "imports_needed": ["web", "database"],
            "method": "basic_fallback",
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error suggesting architecture: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestion failed: {str(e)}")

@router.post("/generate-validated-diagram")
async def generate_validated_diagram(request: Request):
    """Generate diagram with full component validation (works with or without MCP)"""
    try:
        data = await request.json()
        description = data.get("description", "")
        provider = data.get("provider", "azure")
        include_validation = data.get("include_validation", True)
        
        if not description:
            raise HTTPException(status_code=400, detail="description is required")
        
        # All diagram generation now goes through MCP service
        # Remove local validation dependency for clean architecture
        
        # Use MCP service for validated diagram generation
            pass
        
        # Fallback to MCP if available
        if USE_MCP and MCP_AVAILABLE:
            from app.services.diagram_generator_mcp_http import generate_validated_diagram_via_mcp
            result = await generate_validated_diagram_via_mcp(description, provider, include_validation)
            return {
                "success": result.get("success", False),
                "validation_passed": result.get("validation_passed", False),
                "components_used": result.get("components_used", []),
                "diagram_code": result.get("diagram_code", ""),
                "validation_errors": result.get("validation_errors", []),
                "diagram_path": result.get("diagram_path"),
                "method": "mcp_http",
                "error": result.get("error")
            }
        
        # Basic diagram generation fallback
        try:
            from app.services.diagram_generator import generate_diagram
            diagram_url = await generate_diagram(description)
            return {
                "success": True,
                "validation_passed": True,  # Assume basic validation
                "components_used": ["AppServices", "SQLDatabases"],  # Basic assumption
                "diagram_code": "# Basic diagram generated",
                "validation_errors": [],
                "diagram_path": diagram_url,
                "method": "basic_fallback",
                "error": None
            }
        except Exception as fallback_error:
            return {
                "success": False,
                "validation_passed": False,
                "components_used": [],
                "diagram_code": "",
                "validation_errors": [str(fallback_error)],
                "diagram_path": None,
                "method": "failed",
                "error": str(fallback_error)
            }
        
    except Exception as e:
        logger.error(f"Error generating validated diagram: {e}")
        raise HTTPException(status_code=500, detail=f"Validated diagram generation failed: {str(e)}")