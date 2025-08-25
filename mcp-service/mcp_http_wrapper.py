#!/usr/bin/env python3
"""
MCP HTTP Wrapper Service
Wraps the stdio-based MCP diagram server with a REST API interface
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Diagrams HTTP Service",
    description="HTTP wrapper for MCP diagrams stdio server",
    version="1.0.0"
)

class MCPRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class MCPService:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.mcp_server_path = self.base_dir / "mcp_diagrams_server.py"
        self.python_exe = sys.executable
        
        # Verify MCP server exists
        if not self.mcp_server_path.exists():
            raise FileNotFoundError(f"MCP server not found: {self.mcp_server_path}")
    
    async def call_mcp(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the MCP stdio server with proper protocol handshake"""
        try:
            logger.info(f"Calling MCP method: {method}")
            
            # Start MCP server process
            process = await asyncio.create_subprocess_exec(
                self.python_exe,
                str(self.mcp_server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.base_dir)
            )
            
            # MCP Protocol: First initialize the connection
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-http-wrapper",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send initialize request
            init_data = json.dumps(init_request) + "\n"
            process.stdin.write(init_data.encode())
            await process.stdin.drain()
            
            # Read initialize response
            init_response = await process.stdout.readline()
            init_result = json.loads(init_response.decode().strip())
            
            if "error" in init_result:
                raise Exception(f"MCP initialization failed: {init_result['error']}")
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            init_notif_data = json.dumps(initialized_notification) + "\n"
            process.stdin.write(init_notif_data.encode())
            await process.stdin.drain()
            
            # Now send the actual request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": params or {}
            }
            
            request_data = json.dumps(mcp_request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # Close stdin to signal completion
            process.stdin.close()
            
            # Read all responses
            responses = []
            while True:
                try:
                    line = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
                    if not line:
                        break
                    response_text = line.decode().strip()
                    if response_text:
                        response_data = json.loads(response_text)
                        responses.append(response_data)
                        # If this is our main response (id=2), we can break
                        if response_data.get("id") == 2:
                            break
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for MCP response")
                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse response line: {response_text}")
                    continue
            
            # Wait for process to complete
            await process.wait()
            
            # Find our response
            main_response = None
            for response in responses:
                if response.get("id") == 2:
                    main_response = response
                    break
            
            if not main_response:
                # Look for any response with our method
                error_msg = f"No response found for method: {method}"
                if responses:
                    error_msg += f". Got responses: {responses}"
                raise Exception(error_msg)
            
            logger.info(f"MCP response received for method: {method}")
            return main_response
                
        except Exception as e:
            logger.error(f"Error calling MCP: {e}")
            raise e

# Global MCP service instance
mcp_service = MCPService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-http-wrapper"}

@app.post("/mcp/tools/list", response_model=MCPResponse)
async def list_tools():
    """List available MCP tools"""
    try:
        result = await mcp_service.call_mcp("tools/list")
        return MCPResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/mcp/tools/call", response_model=MCPResponse)
async def call_tool(request: Dict[str, Any]):
    """Call an MCP tool"""
    try:
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        result = await mcp_service.call_mcp("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        return MCPResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/mcp/generate-diagram")
async def generate_diagram(request: Dict[str, Any]):
    """Generate a diagram using MCP tools"""
    try:
        # Extract parameters
        architecture_description = request.get("architecture_description", "")
        diagram_code = request.get("diagram_code", "")
        
        if not architecture_description and not diagram_code:
            raise ValueError("Either architecture_description or diagram_code is required")
        
        # If we have an architecture description, first get diagram structure suggestion
        if architecture_description and not diagram_code:
            print(f"🧠 Getting diagram structure for: {architecture_description[:100]}...")
            
            # Call suggest_diagram_structure first
            structure_result = await mcp_service.call_mcp("tools/call", {
                "name": "suggest_diagram_structure",
                "arguments": {
                    "description": architecture_description,
                    "provider_preference": "azure",
                    "complexity_level": "medium"
                }
            })
            
            # Extract suggested code from the structure result
            if "result" in structure_result and "content" in structure_result["result"]:
                content = structure_result["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    suggested_text = content[0].get("text", "")
                    
                    # Try to extract Python code from the response
                    import re
                    code_pattern = r'```python\n(.*?)\n```'
                    code_match = re.search(code_pattern, suggested_text, re.DOTALL)
                    
                    if code_match:
                        diagram_code = code_match.group(1)
                        print(f"✅ Extracted diagram code ({len(diagram_code)} chars)")
                    else:
                        # If no code blocks found, assume the whole response is code
                        diagram_code = suggested_text
                        print(f"⚠️ No code block found, using full response as code")
        
        if not diagram_code:
            raise ValueError("Could not generate or extract diagram code")
        
        print(f"🎨 Generating diagram with code...")
        
        # Now call generate_diagram with the code
        result = await mcp_service.call_mcp("tools/call", {
            "name": "generate_diagram",
            "arguments": {
                "code": diagram_code,
                "format": "png"
            }
        })
        
        return MCPResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error generating diagram: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/mcp/analyze-architecture")
async def analyze_architecture(request: Dict[str, Any]):
    """Analyze architecture using MCP tools"""
    try:
        diagram_code = request.get("diagram_code", "")
        
        if not diagram_code:
            raise ValueError("diagram_code is required")
        
        # Call the analyze_architecture tool
        result = await mcp_service.call_mcp("tools/call", {
            "name": "analyze_architecture", 
            "arguments": {
                "diagram_code": diagram_code
            }
        })
        
        return MCPResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error analyzing architecture: {e}")
        return MCPResponse(success=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_HTTP_PORT", "8001"))
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    
    logger.info(f"Starting MCP HTTP Wrapper on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
