#!/usr/bin/env python3
"""
Enhanced MCP Server for Multi-Provider Architecture Diagrams
Comprehensive access to Python diagrams library and GraphViz tools
Supports ALL providers, advanced features, and custom styling
"""

import json
import os
import tempfile
import traceback
import importlib
from typing import Dict, List, Any, Optional
import uuid
from pathlib import Path

# MCP Server imports
from mcp.server import Server
from mcp.types import Tool, TextContent

# Core diagram imports
try:
    from diagrams import Diagram, Cluster, Edge
    from diagrams.custom import Custom
    
    # Dynamic provider imports
    AVAILABLE_PROVIDERS = [
        'aws', 'azure', 'gcp', 'k8s', 'alibabacloud', 'digitalocean',
        'elastic', 'firebase', 'ibm', 'oci', 'openstack', 'outscale',
        'onprem', 'saas', 'programming', 'generic', 'c4'
    ]
    
    DIAGRAMS_AVAILABLE = True
    
except ImportError as e:
    print(f"Diagrams not available: {e}")
    DIAGRAMS_AVAILABLE = False
    AVAILABLE_PROVIDERS = []

app = Server("enhanced-diagrams")

# Comprehensive service mappings for all providers
PROVIDER_SERVICE_MAPPINGS = {
    'aws': {
        # Compute
        'ec2': 'diagrams.aws.compute.EC2',
        'lambda': 'diagrams.aws.compute.Lambda',
        'ecs': 'diagrams.aws.compute.ECS',
        'eks': 'diagrams.aws.compute.EKS',
        'fargate': 'diagrams.aws.compute.Fargate',
        
        # Database
        'rds': 'diagrams.aws.database.RDS',
        'dynamodb': 'diagrams.aws.database.Dynamodb',
        'redshift': 'diagrams.aws.database.Redshift',
        'elasticache': 'diagrams.aws.database.ElastiCache',
        
        # Storage
        's3': 'diagrams.aws.storage.S3',
        'efs': 'diagrams.aws.storage.EFS',
        'fsx': 'diagrams.aws.storage.FSx',
        
        # Network
        'elb': 'diagrams.aws.network.ELB',
        'alb': 'diagrams.aws.network.ALB',
        'cloudfront': 'diagrams.aws.network.CloudFront',
        'route53': 'diagrams.aws.network.Route53',
        'vpc': 'diagrams.aws.network.VPC',
        
        # Analytics
        'kinesis': 'diagrams.aws.analytics.Kinesis',
        'glue': 'diagrams.aws.analytics.Glue',
        'athena': 'diagrams.aws.analytics.Athena',
    },
    
    'azure': {
        # Compute
        'app services': 'diagrams.azure.web.AppServices',
        'function apps': 'diagrams.azure.web.FunctionApps',
        'virtual machines': 'diagrams.azure.compute.VirtualMachines',
        'kubernetes services': 'diagrams.azure.compute.KubernetesServices',
        
        # Database
        'sql database': 'diagrams.azure.database.SQLDatabases',
        'cosmos db': 'diagrams.azure.database.CosmosDb',
        'mysql': 'diagrams.azure.database.DatabaseForMySQLServers',
        
        # Storage
        'storage accounts': 'diagrams.azure.storage.StorageAccounts',
        'blob storage': 'diagrams.azure.storage.BlobStorage',
        
        # Security
        'key vault': 'diagrams.azure.security.KeyVaults',
        
        # Network
        'load balancer': 'diagrams.azure.network.LoadBalancers',
        'virtual network': 'diagrams.azure.network.VirtualNetworks',
    },
    
    'gcp': {
        # Compute
        'compute engine': 'diagrams.gcp.compute.ComputeEngine',
        'app engine': 'diagrams.gcp.compute.AppEngine',
        'gke': 'diagrams.gcp.compute.GKE',
        'cloud functions': 'diagrams.gcp.compute.Functions',
        
        # Database
        'cloud sql': 'diagrams.gcp.database.SQL',
        'bigtable': 'diagrams.gcp.database.BigTable',
        'firestore': 'diagrams.gcp.database.Firestore',
        
        # Storage
        'cloud storage': 'diagrams.gcp.storage.GCS',
        'persistent disk': 'diagrams.gcp.storage.PersistentDisk',
        
        # Analytics
        'bigquery': 'diagrams.gcp.analytics.BigQuery',
        'pubsub': 'diagrams.gcp.analytics.PubSub',
        'dataflow': 'diagrams.gcp.analytics.Dataflow',
    },
    
    'k8s': {
        # Compute
        'pod': 'diagrams.k8s.compute.Pod',
        'deployment': 'diagrams.k8s.compute.Deployment',
        'replica set': 'diagrams.k8s.compute.ReplicaSet',
        'daemon set': 'diagrams.k8s.compute.DaemonSet',
        'job': 'diagrams.k8s.compute.Job',
        
        # Network
        'service': 'diagrams.k8s.network.Service',
        'ingress': 'diagrams.k8s.network.Ingress',
        'network policy': 'diagrams.k8s.network.NetworkPolicy',
        
        # Storage
        'persistent volume': 'diagrams.k8s.storage.PersistentVolume',
        'storage class': 'diagrams.k8s.storage.StorageClass',
        
        # Config
        'config map': 'diagrams.k8s.config.ConfigMap',
        'secret': 'diagrams.k8s.config.Secret',
    },
    
    'onprem': {
        # Compute
        'server': 'diagrams.onprem.compute.Server',
        'nomad': 'diagrams.onprem.compute.Nomad',
        
        # Database
        'postgresql': 'diagrams.onprem.database.PostgreSQL',
        'mysql': 'diagrams.onprem.database.MySQL',
        'mongodb': 'diagrams.onprem.database.MongoDB',
        'redis': 'diagrams.onprem.inmemory.Redis',
        
        # Network
        'nginx': 'diagrams.onprem.network.Nginx',
        'apache': 'diagrams.onprem.network.Apache',
        'consul': 'diagrams.onprem.network.Consul',
        
        # Queue
        'kafka': 'diagrams.onprem.queue.Kafka',
        'rabbitmq': 'diagrams.onprem.queue.RabbitMQ',
        
        # Monitoring
        'prometheus': 'diagrams.onprem.monitoring.Prometheus',
        'grafana': 'diagrams.onprem.monitoring.Grafana',
        'elasticsearch': 'diagrams.elastic.elasticsearch.Elasticsearch',
    },
    
    'saas': {
        # Communication
        'slack': 'diagrams.saas.communication.Slack',
        'teams': 'diagrams.saas.communication.Teams',
        'zoom': 'diagrams.saas.communication.Zoom',
        
        # Analytics
        'snowflake': 'diagrams.saas.analytics.Snowflake',
        'databricks': 'diagrams.saas.analytics.Databricks',
        
        # Security
        'okta': 'diagrams.saas.security.Okta',
        'auth0': 'diagrams.saas.security.Auth0',
        
        # Monitoring
        'datadog': 'diagrams.saas.monitoring.Datadog',
        'newrelic': 'diagrams.saas.monitoring.Newrelic',
        'pagerduty': 'diagrams.saas.monitoring.Pagerduty',
    },
    
    'programming': {
        # Languages
        'python': 'diagrams.programming.language.Python',
        'java': 'diagrams.programming.language.Java',
        'nodejs': 'diagrams.programming.language.NodeJS',
        'go': 'diagrams.programming.language.Go',
        'rust': 'diagrams.programming.language.Rust',
        'typescript': 'diagrams.programming.language.TypeScript',
        
        # Frameworks
        'react': 'diagrams.programming.framework.React',
        'angular': 'diagrams.programming.framework.Angular',
        'vue': 'diagrams.programming.framework.Vue',
        'django': 'diagrams.programming.framework.Django',
        'spring': 'diagrams.programming.framework.Spring',
        'flutter': 'diagrams.programming.framework.Flutter',
    }
}

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools for comprehensive diagram generation"""
    return [
        Tool(
            name="validate_diagram_code",
            description="Validate Python diagrams code syntax and imports for any provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python diagrams code to validate"},
                    "provider": {"type": "string", "description": "Target provider (aws, azure, gcp, k8s, onprem, etc.)"},
                    "architecture_description": {"type": "string", "description": "Original architecture description"}
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="generate_diagram",
            description="Generate diagram image with advanced styling options",
            inputSchema={
                "type": "object", 
                "properties": {
                    "code": {"type": "string", "description": "Valid Python diagrams code"},
                    "output_path": {"type": "string", "description": "Output file path (optional)"},
                    "format": {"type": "string", "enum": ["png", "svg", "pdf"], "description": "Output format"},
                    "theme": {"type": "string", "description": "Visual theme/style"}
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="get_available_services",
            description="Get comprehensive list of available services across all providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "description": "Provider name (aws, azure, gcp, k8s, onprem, saas, programming)"},
                    "category": {"type": "string", "description": "Service category (compute, database, storage, etc.)"},
                    "search_term": {"type": "string", "description": "Search for specific services"}
                }
            }
        ),
        Tool(
            name="auto_fix_diagram_code",
            description="Automatically fix diagram code issues across all providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python diagrams code to fix"},
                    "target_provider": {"type": "string", "description": "Target provider for optimization"},
                    "architecture_description": {"type": "string", "description": "Original architecture description"}
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="suggest_diagram_structure",
            description="AI-powered diagram structure suggestions for any architecture",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Architecture description"},
                    "provider_preference": {"type": "string", "description": "Preferred cloud provider"},
                    "architecture_type": {"type": "string", "description": "Type (microservices, monolith, serverless, etc.)"},
                    "complexity_level": {"type": "string", "enum": ["simple", "medium", "complex"], "description": "Diagram complexity"}
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="create_cluster_diagram",
            description="Create diagrams with advanced clustering and grouping",
            inputSchema={
                "type": "object",
                "properties": {
                    "cluster_config": {"type": "object", "description": "Cluster configuration"},
                    "services": {"type": "array", "description": "Services to include"},
                    "connections": {"type": "array", "description": "Service connections"}
                },
                "required": ["cluster_config", "services"]
            }
        ),
        Tool(
            name="generate_multi_provider_diagram",
            description="Create diagrams spanning multiple cloud providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "providers": {"type": "array", "items": {"type": "string"}, "description": "List of providers to include"},
                    "architecture_description": {"type": "string", "description": "Multi-cloud architecture description"},
                    "hybrid_components": {"type": "array", "description": "On-prem/hybrid components"}
                },
                "required": ["providers", "architecture_description"]
            }
        ),
        Tool(
            name="create_custom_node_diagram",
            description="Create diagrams with custom nodes and icons",
            inputSchema={
                "type": "object",
                "properties": {
                    "custom_nodes": {"type": "array", "description": "Custom node definitions"},
                    "icon_urls": {"type": "array", "description": "URLs or paths to custom icons"},
                    "base_diagram_code": {"type": "string", "description": "Base diagram code"}
                },
                "required": ["custom_nodes"]
            }
        ),
        Tool(
            name="generate_graphviz_diagram",
            description="Direct GraphViz diagram generation with advanced features",
            inputSchema={
                "type": "object",
                "properties": {
                    "dot_code": {"type": "string", "description": "GraphViz DOT notation code"},
                    "layout_engine": {"type": "string", "enum": ["dot", "neato", "fdp", "sfdp", "circo", "twopi"], "description": "GraphViz layout engine"},
                    "output_format": {"type": "string", "enum": ["png", "svg", "pdf", "ps"], "description": "Output format"}
                },
                "required": ["dot_code"]
            }
        ),
        Tool(
            name="export_diagram_templates",
            description="Export reusable diagram templates and patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_type": {"type": "string", "description": "Template type (microservices, serverless, etc.)"},
                    "provider": {"type": "string", "description": "Target provider"},
                    "customizations": {"type": "object", "description": "Template customizations"}
                },
                "required": ["template_type"]
            }
        ),
        Tool(
            name="validate_azure_components",
            description="Validate Azure component names against the diagrams library",
            inputSchema={
                "type": "object",
                "properties": {
                    "component_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Azure component names to validate"
                    }
                },
                "required": ["component_names"]
            }
        ),
        Tool(
            name="suggest_architecture_components",
            description="Suggest validated Azure components based on architecture description",
            inputSchema={
                "type": "object", 
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Architecture description to analyze"
                    },
                    "provider": {
                        "type": "string",
                        "default": "azure",
                        "description": "Cloud provider (currently supports 'azure')"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="generate_validated_diagram",
            description="Generate a complete validated diagram with proper imports and components",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string", 
                        "description": "Architecture description"
                    },
                    "provider": {
                        "type": "string",
                        "default": "azure",
                        "description": "Cloud provider"
                    }
                },
                "required": ["description"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Enhanced tool call handler with comprehensive functionality"""
    
    try:
        if name == "validate_diagram_code":
            result = await validate_diagram_code(
                arguments["code"], 
                arguments.get("provider", "auto"),
                arguments.get("architecture_description", "")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "generate_diagram":
            result = await generate_diagram(
                arguments["code"],
                arguments.get("output_path"),
                arguments.get("format", "png"),
                arguments.get("theme")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_available_services":
            result = get_available_services(
                arguments.get("provider"),
                arguments.get("category"),
                arguments.get("search_term")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "auto_fix_diagram_code":
            result = auto_fix_diagram_code(
                arguments["code"],
                arguments.get("target_provider"),
                arguments.get("architecture_description", "")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "suggest_diagram_structure":
            result = suggest_diagram_structure(
                arguments["description"],
                arguments.get("provider_preference"),
                arguments.get("architecture_type"),
                arguments.get("complexity_level", "medium")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "create_cluster_diagram":
            result = create_cluster_diagram(
                arguments["cluster_config"],
                arguments["services"],
                arguments.get("connections", [])
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "generate_multi_provider_diagram":
            result = generate_multi_provider_diagram(
                arguments["providers"],
                arguments["architecture_description"],
                arguments.get("hybrid_components", [])
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "create_custom_node_diagram":
            result = create_custom_node_diagram(
                arguments["custom_nodes"],
                arguments.get("icon_urls", []),
                arguments.get("base_diagram_code", "")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "generate_graphviz_diagram":
            result = generate_graphviz_diagram(
                arguments["dot_code"],
                arguments.get("layout_engine", "dot"),
                arguments.get("output_format", "png")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "export_diagram_templates":
            result = export_diagram_templates(
                arguments["template_type"],
                arguments.get("provider"),
                arguments.get("customizations", {})
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "validate_azure_components":
            try:
                from enhanced_azure_validator import validate_component_names
                result = validate_component_names(arguments["component_names"])
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except ImportError:
                error_result = {"success": False, "error": "Azure validator not available"}
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        elif name == "suggest_architecture_components":
            try:
                from enhanced_azure_validator import suggest_architecture_components
                result = suggest_architecture_components(
                    arguments["description"],
                    arguments.get("provider", "azure")
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except ImportError:
                error_result = {"success": False, "error": "Azure validator not available"}
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        elif name == "generate_validated_diagram":
            try:
                from enhanced_azure_validator import generate_validated_diagram
                result = generate_validated_diagram(
                    arguments["description"],
                    arguments.get("provider", "azure")
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except ImportError:
                error_result = {"success": False, "error": "Azure validator not available"}
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Tool execution failed: {str(e)}",
            "traceback": traceback.format_exc()
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def validate_diagram_code(code: str, provider: str = "auto", architecture_description: str = "") -> Dict[str, Any]:
    """Enhanced validation supporting all providers"""
    
    if not DIAGRAMS_AVAILABLE:
        return {
            "is_valid": False,
            "validation_score": 0,
            "errors": ["Diagrams library not available on server"],
            "warnings": [],
            "suggestions": ["Install diagrams library: pip install diagrams graphviz"],
            "provider_detected": None,
            "supported_features": []
        }
    
    errors = []
    warnings = []
    suggestions = []
    score = 100
    detected_provider = detect_provider_from_code(code)
    
    try:
        # Enhanced syntax and import validation
        compile(code, '<string>', 'exec')
        
        # Validate imports dynamically
        import_errors = validate_imports(code)
        if import_errors:
            errors.extend(import_errors)
            score -= len(import_errors) * 10
        
        # Check for advanced features usage
        advanced_features = detect_advanced_features(code)
        
        # Provider-specific validation
        if detected_provider and detected_provider in PROVIDER_SERVICE_MAPPINGS:
            provider_suggestions = validate_provider_services(code, detected_provider)
            suggestions.extend(provider_suggestions)
        
        # Best practices check
        if 'show=False' not in code:
            warnings.append("Consider adding show=False to prevent GUI display")
            score -= 5
            
        if 'Cluster(' not in code and len(code.split('\n')) > 10:
            suggestions.append("Consider using Clusters for better organization in complex diagrams")
        
        return {
            "is_valid": len(errors) == 0,
            "validation_score": score,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "provider_detected": detected_provider,
            "advanced_features_detected": advanced_features,
            "corrected_code": code,
            "explanation": f"Validation complete: {len(errors)} errors, {len(warnings)} warnings"
        }
        
    except Exception as e:
        errors.append(f"Validation error: {e}")
        return {
            "is_valid": False,
            "validation_score": 20,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "provider_detected": detected_provider,
            "corrected_code": code,
            "explanation": f"Validation failed with {len(errors)} errors"
        }

def get_available_services(provider: str = None, category: str = None, search_term: str = None) -> Dict[str, Any]:
    """Get comprehensive service listings across all providers"""
    
    if provider and provider not in PROVIDER_SERVICE_MAPPINGS:
        return {
            "error": f"Provider '{provider}' not supported",
            "available_providers": list(PROVIDER_SERVICE_MAPPINGS.keys())
        }
    
    result = {}
    
    if provider:
        services = PROVIDER_SERVICE_MAPPINGS[provider]
        if search_term:
            services = {k: v for k, v in services.items() if search_term.lower() in k.lower()}
        result[provider] = services
    else:
        result = PROVIDER_SERVICE_MAPPINGS.copy()
    
    # Add metadata
    result["metadata"] = {
        "total_providers": len(PROVIDER_SERVICE_MAPPINGS),
        "total_services": sum(len(services) for services in PROVIDER_SERVICE_MAPPINGS.values()),
        "supported_features": [
            "Multi-provider diagrams",
            "Custom nodes and icons", 
            "Advanced clustering",
            "Edge styling and labels",
            "Multiple output formats",
            "GraphViz integration"
        ]
    }
    
    return result

# Additional implementation functions would go here...
# (detect_provider_from_code, validate_imports, create_cluster_diagram, etc.)

def detect_provider_from_code(code: str) -> Optional[str]:
    """Detect which provider is being used in the diagram code"""
    for provider in AVAILABLE_PROVIDERS:
        if f'diagrams.{provider}.' in code:
            return provider
    return None

def detect_advanced_features(code: str) -> List[str]:
    """Detect advanced features being used in the code"""
    features = []
    
    if 'Cluster(' in code:
        features.append("clustering")
    if 'Edge(' in code:
        features.append("custom_edges")
    if 'Custom(' in code:
        features.append("custom_nodes")
    if 'graph_attr=' in code or 'node_attr=' in code or 'edge_attr=' in code:
        features.append("custom_styling")
    if 'direction=' in code:
        features.append("layout_control")
    
    return features

def validate_imports(code: str) -> List[str]:
    """Validate all import statements in the code"""
    import_errors = []
    
    # Extract import statements
    import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('from diagrams')]
    
    for line in import_lines:
        try:
            exec(line)
        except ImportError as e:
            import_errors.append(f"Import error in '{line}': {str(e)}")
        except Exception as e:
            import_errors.append(f"Error in '{line}': {str(e)}")
    
    return import_errors

def validate_provider_services(code: str, provider: str) -> List[str]:
    """Validate services used match the provider's available services"""
    suggestions = []
    
    if provider in PROVIDER_SERVICE_MAPPINGS:
        available_services = PROVIDER_SERVICE_MAPPINGS[provider]
        
        # Check for common misnamed services
        for service_name in available_services:
            variations = [
                service_name.replace('_', ''),
                service_name.replace('_', ' '),
                service_name.title(),
                service_name.upper()
            ]
            
            for variation in variations:
                if variation in code and service_name not in code:
                    suggestions.append(f"Consider using '{service_name}' instead of '{variation}'")
    
    return suggestions

# Template and advanced generation functions
def generate_sample_code_advanced(services: List[Dict], connections: List[str], use_clusters: bool = True) -> str:
    """Generate advanced sample diagram code with clustering and styling"""
    
    if not services:
        return ""
    
    # Group services by provider
    provider_groups = {}
    for service in services:
        provider = service.get("provider", "unknown")
        if provider not in provider_groups:
            provider_groups[provider] = []
        provider_groups[provider].append(service)
    
    # Generate imports
    imports = ["from diagrams import Diagram, Cluster, Edge"]
    module_imports = {}
    
    for service in services:
        module = service["module"]
        service_class = service["service_class"]
        
        if module not in module_imports:
            module_imports[module] = []
        if service_class not in module_imports[module]:
            module_imports[module].append(service_class)
    
    for module, classes in module_imports.items():
        imports.append(f"from {module} import {', '.join(classes)}")
    
    # Generate diagram with advanced features
    code_lines = imports + ["", 'with Diagram("Multi-Provider Architecture", show=False, graph_attr={"fontsize": "45", "fontcolor": "darkblue"}):']
    
    if use_clusters and len(provider_groups) > 1:
        # Generate clustered structure
        for provider, provider_services in provider_groups.items():
            code_lines.append(f'    with Cluster("{provider.upper()} Services"):')
            for service in provider_services:
                var_name = service["keyword"].replace(" ", "_").replace("-", "_")
                code_lines.append(f'        {var_name} = {service["service_class"]}("{service["keyword"].title()}")')
    else:
        # Generate flat structure
        for service in services:
            var_name = service["keyword"].replace(" ", "_").replace("-", "_")
            code_lines.append(f'    {var_name} = {service["service_class"]}("{service["keyword"].title()}")')
    
    # Add styled connections
    if connections:
        code_lines.append("")
        code_lines.append("    # Connections with custom styling")
        for i, connection in enumerate(connections):
            if i % 2 == 0:
                code_lines.append(f"    {connection} >> Edge(color='darkgreen', style='bold')")
            else:
                code_lines.append(f"    {connection}")
    
    return "\n".join(code_lines)

# Additional helper functions for the enhanced features...
async def generate_diagram(code: str, output_path: str = None, format: str = "png", theme: str = None) -> Dict[str, Any]:
    """Enhanced diagram generation with multiple formats and themes"""
    try:
        # Create unique output path if not provided
        if not output_path:
            import uuid
            output_path = f"/tmp/diagram_{uuid.uuid4().hex}.{format}"
        
        # Prepare environment for code execution
        import os
        import sys
        from io import StringIO
        import tempfile
        
        # Create a temporary directory for diagram generation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the full path for the diagram
            diagram_filename = f"diagram.{format}"
            full_output_path = os.path.join(temp_dir, diagram_filename)
            
            # Use forward slashes for cross-platform compatibility
            temp_dir_safe = temp_dir.replace('\\', '/')
            diagram_path_safe = f"{temp_dir_safe}/diagram"
            
            # Modify the code to use the correct output path
            modified_code = code
            
            # If filename is not already specified, add it
            if 'filename=' not in modified_code:
                # Replace the Diagram(...) call to include the filename
                if 'with Diagram(' in modified_code:
                    # Find the Diagram constructor and add filename parameter
                    lines = modified_code.split('\n')
                    for i, line in enumerate(lines):
                        if 'with Diagram(' in line and 'filename=' not in line:
                            # Insert filename parameter before show=False or at the end
                            if 'show=False' in line:
                                lines[i] = line.replace('show=False', f'filename=r"{diagram_path_safe}", show=False')
                            else:
                                # Add filename parameter before the closing parenthesis
                                if line.rstrip().endswith('):'):
                                    lines[i] = line.rstrip()[:-2] + f', filename=r"{diagram_path_safe}"):'
                                else:
                                    # Multi-line Diagram call - need to find the closing parenthesis
                                    for j in range(i + 1, len(lines)):
                                        if '):' in lines[j]:
                                            lines[j] = lines[j].replace('):', f', filename=r"{diagram_path_safe}"):', 1)
                                            break
                            break
                    modified_code = '\n'.join(lines)
            
            # Capture stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            try:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                # Execute the diagram code
                exec(modified_code, {'__name__': '__main__'})
                
                # Check if diagram file was created
                expected_file = os.path.join(temp_dir, f"diagram.{format}")
                if os.path.exists(expected_file):
                    # Read the generated file
                    with open(expected_file, 'rb') as f:
                        diagram_data = f.read()
                    
                    # If output_path was provided, save there too
                    if output_path and output_path != expected_file:
                        with open(output_path, 'wb') as f:
                            f.write(diagram_data)
                    
                    return {
                        "success": True,
                        "output_path": expected_file,
                        "format": format,
                        "size_bytes": len(diagram_data),
                        "stdout": stdout_capture.getvalue(),
                        "stderr": stderr_capture.getvalue()
                    }
                else:
                    # Check for other possible output files
                    generated_files = [f for f in os.listdir(temp_dir) if f.endswith(f'.{format}')]
                    if generated_files:
                        actual_file = os.path.join(temp_dir, generated_files[0])
                        with open(actual_file, 'rb') as f:
                            diagram_data = f.read()
                        
                        return {
                            "success": True,
                            "output_path": actual_file,
                            "format": format,
                            "size_bytes": len(diagram_data),
                            "stdout": stdout_capture.getvalue(),
                            "stderr": stderr_capture.getvalue()
                        }
                    else:
                        return {
                            "success": False,
                            "error": "No diagram file was generated",
                            "stdout": stdout_capture.getvalue(),
                            "stderr": stderr_capture.getvalue(),
                            "temp_dir_contents": os.listdir(temp_dir)
                        }
                        
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate diagram: {str(e)}",
            "stdout": stdout_capture.getvalue() if 'stdout_capture' in locals() else "",
            "stderr": stderr_capture.getvalue() if 'stderr_capture' in locals() else ""
        }

def suggest_diagram_structure(description: str, provider_preference: str = None, 
                            architecture_type: str = None, complexity_level: str = "medium") -> Dict[str, Any]:
    """AI-powered structure suggestions based on description and preferences with validated components"""
    try:
        # Import the enhanced validator
        from enhanced_azure_validator import AzureComponentValidator
        
        # Set default provider
        provider = provider_preference or "azure"
        
        if provider == "azure":
            # Use the enhanced validator for Azure components
            validator = AzureComponentValidator()
            suggestions = validator.suggest_components_for_architecture(description, provider)
            
            if suggestions["components"]:
                # Generate validated diagram code
                diagram_code = validator.generate_validated_diagram_code(
                    suggestions["components"], 
                    description
                )
                
                return {
                    "success": True,
                    "diagram_code": diagram_code,
                    "components_detected": [
                        {
                            "id": comp["id"],
                            "type": comp["canonical"],
                            "label": comp["label"],
                            "submodule": comp["submodule"]
                        } for comp in suggestions["components"]
                    ],
                    "provider": provider,
                    "complexity": complexity_level,
                    "validation_passed": True,
                    "imports_needed": suggestions["imports_needed"],
                    "suggestions": [
                        f"Detected {len(suggestions['components'])} validated components",
                        f"Using {provider} provider with canonical component names",
                        "All components verified against diagrams library",
                        "Consider adding monitoring and logging components",
                        "Review security and networking requirements"
                    ]
                }
            else:
                # Fallback to basic detection if no components found
                return _fallback_suggestion(description, provider, complexity_level)
        else:
            # Fallback for non-Azure providers
            return _fallback_suggestion(description, provider, complexity_level)
        
    except Exception as e:
        # Fallback in case of any errors
        return _fallback_suggestion(description, provider_preference or "azure", complexity_level)

def _fallback_suggestion(description: str, provider: str, complexity_level: str) -> Dict[str, Any]:
    """Fallback suggestion method for when enhanced validation fails"""
    description_lower = description.lower()
    
    # Initialize components
    components = []
    
    # Basic architecture parsing and suggestion
    if any(word in description_lower for word in ['react', 'frontend', 'web app', 'spa', 'angular', 'vue']):
        components.append(("frontend", "AppServices", "Web Frontend"))
    
    # Detect backend/API components
    if any(word in description_lower for word in ['backend', 'api', 'node.js', 'nodejs', 'express', 'fastapi', 'python']):
        components.append(("backend", "AppServices", "Backend API"))
    
    # Detect database components
    if any(word in description_lower for word in ['database', 'db', 'postgresql', 'postgres', 'mysql', 'sql']):
        components.append(("database", "DatabaseForPostgresqlServers", "PostgreSQL Database"))
    
    # If no components detected, provide a basic web app structure
    if not components:
        components = [
            ("frontend", "AppServices", "Web Frontend"),
            ("backend", "AppServices", "Backend API"),
            ("database", "SQLDatabases", "Database")
        ]
    
    # Generate Python diagrams code
    diagram_code = f"""from diagrams import Diagram, Edge
from diagrams.azure.web import AppServices as WebAppServices
from diagrams.azure.compute import AppServices as ComputeAppServices  
from diagrams.azure.database import SQLDatabases, DatabaseForPostgresqlServers

with Diagram("{description[:50]}...", show=False, direction="TB"):
"""
    
    # Add components
    for comp_id, comp_class, comp_label in components:
        if comp_class == "AppServices" and comp_id == "frontend":
            diagram_code += f"    {comp_id} = WebAppServices(\"{comp_label}\")\n"
        elif comp_class == "AppServices" and comp_id == "backend":
            diagram_code += f"    {comp_id} = ComputeAppServices(\"{comp_label}\")\n"
        else:
            diagram_code += f"    {comp_id} = {comp_class}(\"{comp_label}\")\n"
    
    # Add basic connections
    if len(components) >= 2:
        diagram_code += "\n    # Connections\n"
        for i in range(len(components) - 1):
            curr_id = components[i][0]
            next_id = components[i + 1][0]
            diagram_code += f"    {curr_id} >> {next_id}\n"
    
    return {
        "success": True,
        "diagram_code": diagram_code,
        "components_detected": [{"id": c[0], "type": c[1], "label": c[2]} for c in components],
        "provider": provider,
        "complexity": complexity_level,
        "validation_passed": False,
        "suggestions": [
            f"Detected {len(components)} components using fallback method",
            f"Using {provider} provider components",
            "Component validation not available - using basic detection",
            "Consider adding monitoring and logging components"
        ]
    }

def create_cluster_diagram(cluster_config: Dict, services: List, connections: List = None) -> Dict[str, Any]:
    """Create advanced clustered diagrams"""
    # Implementation for cluster-based diagrams
    pass

def generate_multi_provider_diagram(providers: List[str], architecture_description: str, 
                                  hybrid_components: List = None) -> Dict[str, Any]:
    """Generate diagrams spanning multiple providers"""
    # Implementation for multi-cloud diagrams
    pass

def create_custom_node_diagram(custom_nodes: List, icon_urls: List = None, base_diagram_code: str = "") -> Dict[str, Any]:
    """Create diagrams with custom nodes and icons"""
    # Implementation for custom node support
    pass

def generate_graphviz_diagram(dot_code: str, layout_engine: str = "dot", output_format: str = "png") -> Dict[str, Any]:
    """Direct GraphViz diagram generation"""
    # Implementation for direct GraphViz support
    pass

def export_diagram_templates(template_type: str, provider: str = None, customizations: Dict = None) -> Dict[str, Any]:
    """Export reusable diagram templates"""
    # Implementation for template system
    pass

def auto_fix_diagram_code(code: str, target_provider: str = "azure", architecture_description: str = "") -> Dict[str, Any]:
    """Auto-fix common diagram code issues"""
    
    original_code = code
    fixes_applied = []
    
    # Fix common class name issues for Azure
    if target_provider == "azure" or not target_provider:
        common_fixes = {
            'AppService': 'AppServices',
            'KeyVault': 'KeyVaults',
            'SqlDatabase': 'SQLDatabases',
            'StorageAccount': 'StorageAccounts',
            'VirtualMachine': 'VirtualMachines',
            'NetworkSecurityGroup': 'NetworkSecurityGroups',
        }
        
        for old, new in common_fixes.items():
            if old in code and new not in code:
                code = code.replace(old, new)
                fixes_applied.append(f"Changed {old} to {new}")
    
    # Add show=False if missing
    if 'with Diagram(' in code and 'show=False' not in code:
        import re
        code = re.sub(r'with Diagram\("([^"]+)"\)', r'with Diagram("\1", show=False)', code)
        fixes_applied.append("Added show=False parameter")
    
    # Match services to architecture description
    if architecture_description:
        suggested_fixes = suggest_service_matches(architecture_description, code)
        if suggested_fixes:
            fixes_applied.extend(suggested_fixes)
    
    return {
        "original_code": original_code,
        "fixed_code": code,
        "fixes_applied": fixes_applied,
        "changes_made": len(fixes_applied) > 0
    }

def suggest_service_matches(description: str, current_code: str) -> List[str]:
    """Suggest service matches based on architecture description"""
    suggestions = []
    description_lower = description.lower()
    
    # Check for mismatches
    if "storage account" in description_lower and "SQLDatabases" in current_code:
        suggestions.append("Consider using StorageAccounts instead of SQLDatabases for storage backend")
    
    if "web app" in description_lower and "AppServices" not in current_code:
        suggestions.append("Add AppServices for web application component")
    
    if "database" in description_lower and "SQLDatabases" not in current_code and "CosmosDb" not in current_code:
        suggestions.append("Consider adding SQLDatabases or CosmosDb for database component")
    
    if "security" in description_lower and "KeyVaults" not in current_code:
        suggestions.append("Consider adding KeyVaults for secure credential storage")
    
    return suggestions

if __name__ == "__main__":
    import asyncio
    
    async def main():
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    asyncio.run(main())