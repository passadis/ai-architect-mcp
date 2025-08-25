# Enhanced diagram generator with validation integration
import os
import asyncio
from .validation_agent import validate_diagram_code

async def generate_and_validate_diagram(architecture_description: str, design_document: str = "") -> dict:
    """
    Generate diagram with validation loop
    
    Returns:
        dict: {
            'success': bool,
            'diagram_path': str or None,
            'validation_results': dict,
            'final_code': str,
            'iterations': int,
            'code': str (for compatibility)
        }
    """
    # Reduced iterations for faster response in production
    max_iterations = 2  # Reduced from 3 to 2
    current_iteration = 0
    validation_results = {}
    last_error = None
    generated_code = None
    
    # Import the diagram generator functions
    from .diagram_generator import generate_diagram_code, render_code_to_image
    import uuid
    import os
    
    while current_iteration < max_iterations:
        current_iteration += 1
        print(f"\n🔄 Diagram Generation Iteration {current_iteration}/{max_iterations}")
        
        try:
            # For first iteration, generate code from diagram agent
            if current_iteration == 1:
                print("🎯 Generating diagram code from agent...")
                generated_code = await generate_diagram_code(architecture_description)
                print(f"📝 Generated code (first {200} chars): {generated_code[:200]}...")
            else:
                # Use corrected code from previous validation
                if validation_results.get('corrected_code'):
                    print("🔧 Using corrected code from validation...")
                    generated_code = validation_results['corrected_code']
                    
                    # Apply additional local fixes to the corrected code
                    from .validation_agent import auto_fix_common_errors
                    locally_fixed_code = auto_fix_common_errors(generated_code)
                    if locally_fixed_code != generated_code:
                        print("🔧 Applied additional local fixes...")
                        generated_code = locally_fixed_code
                else:
                    print("⚠️ No corrected code available, regenerating...")
                    generated_code = await generate_diagram_code(architecture_description)
            
            # Apply local fixes to any generated code
            if current_iteration == 1:
                from .validation_agent import auto_fix_common_errors
                locally_fixed_code = auto_fix_common_errors(generated_code)
                if locally_fixed_code != generated_code:
                    print("🔧 Applied local fixes to first iteration...")
                    generated_code = locally_fixed_code
            
            # Now try to render the code
            try:
                file_uuid = str(uuid.uuid4())
                filename = f"{file_uuid}.png"
                filepath = os.path.join("static", "diagrams", filename)
                
                print("🖼️ Rendering diagram...")
                render_code_to_image(generated_code, filepath, file_uuid)
                
                # Upload to Azure Storage if available
                try:
                    from .storage import upload_diagram
                    diagram_url = await upload_diagram(filepath, filename)
                    
                    if diagram_url and diagram_url != filepath:
                        # Successfully uploaded to Azure Storage
                        print(f"✅ Diagram uploaded to Azure Storage: {diagram_url}")
                        diagram_path = diagram_url
                    else:
                        # Fallback to local path
                        diagram_path = f"/static/diagrams/{filename}"
                        print(f"⚠️ Using local diagram path: {diagram_path}")
                        
                except Exception as upload_error:
                    print(f"⚠️ Error uploading diagram to Azure Storage: {upload_error}")
                    diagram_path = f"/static/diagrams/{filename}"
                
                print(f"✅ Successfully rendered diagram: {diagram_path}")
                
            except Exception as render_error:
                print(f"❌ Failed to render diagram: {render_error}")
                last_error = render_error
                diagram_path = None
            
            # Validate the generated diagram code
            print("🔍 Validating generated diagram code...")
            validation_results = await validate_diagram_code(
                architecture_description, 
                generated_code
            )
            
            print(f"📊 Validation Score: {validation_results['validation_score']}/100")
            print(f"✅ Valid: {validation_results['is_valid']}")
            
            if validation_results['errors']:
                print(f"🔧 Errors found: {validation_results['errors']}")
            if validation_results['warnings']:
                print(f"⚠️ Warnings: {validation_results['warnings']}")
                
            # Check if we have a successful diagram and good validation
            if diagram_path and (validation_results['is_valid'] or validation_results['validation_score'] >= 70):
                print(f"🎉 Diagram validated successfully in {current_iteration} iteration(s)!")
                final_code = validation_results.get('corrected_code', generated_code)
                return {
                    'success': True,
                    'diagram_path': diagram_path,
                    'validation_results': validation_results,
                    'final_code': final_code,
                    'code': final_code,
                    'iterations': current_iteration
                }
            
            elif current_iteration == max_iterations:
                print(f"⚠️ Max iterations reached.")
                # Try to use the corrected code one more time if available
                final_code = validation_results.get('corrected_code', generated_code)
                
                if final_code and final_code != generated_code and not diagram_path:
                    print("🔧 Attempting final render with corrected code...")
                    try:
                        file_uuid = str(uuid.uuid4())
                        filename = f"{file_uuid}.png"
                        filepath = os.path.join("static", "diagrams", filename)
                        
                        render_code_to_image(final_code, filepath, file_uuid)
                        
                        # Upload to Azure Storage if available
                        try:
                            from .storage import upload_diagram
                            diagram_url = await upload_diagram(filepath, filename)
                            
                            if diagram_url and diagram_url != filepath:
                                # Successfully uploaded to Azure Storage
                                final_diagram_path = diagram_url
                                print(f"✅ Final diagram uploaded to Azure Storage: {diagram_url}")
                            else:
                                # Fallback to local path
                                final_diagram_path = f"/static/diagrams/{filename}"
                                print(f"⚠️ Using local diagram path: {final_diagram_path}")
                                
                        except Exception as upload_error:
                            print(f"⚠️ Error uploading final diagram to Azure Storage: {upload_error}")
                            final_diagram_path = f"/static/diagrams/{filename}"
                        
                        return {
                            'success': True,
                            'diagram_path': final_diagram_path,
                            'validation_results': validation_results,
                            'final_code': final_code,
                            'code': final_code,
                            'iterations': current_iteration,
                            'warning': 'Used corrected code from validation after max iterations'
                        }
                    except Exception as final_render_error:
                        print(f"❌ Final render also failed: {final_render_error}")
                        last_error = final_render_error
                
                return {
                    'success': False,
                    'error': f"Max iterations reached. Last error: {last_error or 'Validation failed'}",
                    'validation_results': validation_results,
                    'iterations': current_iteration,
                    'final_code': final_code or generated_code
                }
            
            else:
                print(f"🔧 Iteration {current_iteration} failed. Retrying with corrections...")
                # Continue to next iteration with validation feedback
                
        except Exception as e:
            print(f"❌ Error in iteration {current_iteration}: {e}")
            last_error = e
            
            if current_iteration == max_iterations:
                return {
                    'success': False,
                    'error': str(e),
                    'validation_results': validation_results,
                    'iterations': current_iteration
                }
    
    return {
        'success': False,
        'error': 'Max iterations reached without success',
        'validation_results': validation_results,
        'iterations': max_iterations
    }

# Backward compatibility wrapper
async def enhanced_diagram_route(architecture_description: str, design_document: str = ""):
    """Enhanced route that includes validation - for backward compatibility"""
    try:
        result = await generate_and_validate_diagram(architecture_description, design_document)
        
        if result['success']:
            return {
                "status": "success",
                "message": f"Diagram generated and validated in {result['iterations']} iteration(s)",
                "diagram_path": result['diagram_path'],
                "validation_score": result['validation_results'].get('validation_score', 0),
                "warnings": result['validation_results'].get('warnings', []),
                "suggestions": result['validation_results'].get('suggestions', [])
            }
        else:
            return {
                "status": "error",
                "message": result.get('error', 'Unknown error'),
                "iterations": result['iterations']
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Enhanced diagram generation failed: {str(e)}"
        }
