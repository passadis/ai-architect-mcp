#!/usr/bin/env python3
"""
Enhanced Azure Diagram Generator with Validated Components

Uses the comprehensive azure_nodes.json to ensure all components are valid
and provides intelligent suggestions for alternatives.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class AzureComponentValidator:
    """Validates and suggests Azure diagram components using the canonical list"""
    
    def __init__(self, azure_nodes_path: str = None):
        if azure_nodes_path is None:
            azure_nodes_path = os.path.join(os.path.dirname(__file__), "azure_nodes.json")
        
        with open(azure_nodes_path, 'r', encoding='utf-8') as f:
            self.azure_data = json.load(f)
        
        # Build lookup tables
        self._build_lookups()
    
    def _build_lookups(self):
        """Build efficient lookup tables for validation and suggestions"""
        self.canonical_map = {}  # canonical_name -> (submodule, class_info)
        self.alias_map = {}      # alias -> canonical_name
        self.keyword_map = {}    # keyword -> [(submodule, canonical_name)]
        self.submodule_components = {}  # submodule -> [canonical_names]
        
        for submodule, components in self.azure_data.items():
            self.submodule_components[submodule] = []
            
            for comp in components:
                canonical = comp["canonical"]
                class_name = comp["class"]
                
                # Skip private classes
                if canonical.startswith('_'):
                    continue
                
                self.canonical_map[canonical] = (submodule, comp)
                self.submodule_components[submodule].append(canonical)
                
                # Map aliases
                for alias in comp.get("aliases", []):
                    self.alias_map[alias] = canonical
                
                # Build keyword map for smart suggestions
                keywords = self._extract_keywords(canonical)
                for keyword in keywords:
                    if keyword not in self.keyword_map:
                        self.keyword_map[keyword] = []
                    self.keyword_map[keyword].append((submodule, canonical))
    
    def _extract_keywords(self, name: str) -> List[str]:
        """Extract searchable keywords from component names"""
        import re
        # Split camelCase and handle common patterns
        words = re.findall(r'[A-Z][a-z]*|[a-z]+', name)
        keywords = [w.lower() for w in words]
        
        # Add full name variations
        keywords.extend([
            name.lower(),
            name.lower().replace('services', '').replace('service', ''),
            name.lower().replace('apps', '').replace('app', ''),
        ])
        
        return list(set(keywords))
    
    def validate_component(self, name: str) -> Dict[str, Any]:
        """Validate a component name and provide suggestions"""
        # Direct canonical match
        if name in self.canonical_map:
            submodule, comp_info = self.canonical_map[name]
            return {
                "valid": True,
                "canonical": name,
                "submodule": submodule,
                "class": comp_info["class"],
                "import_path": f"diagrams.azure.{submodule}",
                "aliases": comp_info.get("aliases", [])
            }
        
        # Alias match
        if name in self.alias_map:
            canonical = self.alias_map[name]
            submodule, comp_info = self.canonical_map[canonical]
            return {
                "valid": True,
                "canonical": canonical,
                "submodule": submodule,
                "class": comp_info["class"],
                "import_path": f"diagrams.azure.{submodule}",
                "aliases": comp_info.get("aliases", []),
                "note": f"'{name}' is an alias for '{canonical}'"
            }
        
        # Not found - provide suggestions
        suggestions = self._find_suggestions(name)
        return {
            "valid": False,
            "requested": name,
            "suggestions": suggestions,
            "error": f"Component '{name}' not found in Azure diagrams library"
        }
    
    def _find_suggestions(self, name: str) -> List[Dict[str, str]]:
        """Find similar component names"""
        name_lower = name.lower()
        suggestions = []
        
        # Keyword-based matching
        for keyword in self._extract_keywords(name):
            if keyword in self.keyword_map:
                for submodule, canonical in self.keyword_map[keyword]:
                    suggestions.append({
                        "name": canonical,
                        "submodule": submodule,
                        "reason": f"matches keyword '{keyword}'"
                    })
        
        # Fuzzy string matching for close names
        for canonical in self.canonical_map:
            if self._similarity_score(name_lower, canonical.lower()) > 0.6:
                submodule, _ = self.canonical_map[canonical]
                suggestions.append({
                    "name": canonical,
                    "submodule": submodule,
                    "reason": "similar name"
                })
        
        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg["name"] not in seen:
                seen.add(sugg["name"])
                unique_suggestions.append(sugg)
        
        return unique_suggestions[:5]  # Top 5 suggestions
    
    def _similarity_score(self, a: str, b: str) -> float:
        """Simple similarity score based on common characters"""
        if not a or not b:
            return 0.0
        
        common = sum(1 for char in a if char in b)
        return common / max(len(a), len(b))
    
    def suggest_components_for_architecture(self, description: str, 
                                         provider: str = "azure") -> Dict[str, Any]:
        """Suggest appropriate components based on architecture description"""
        description_lower = description.lower()
        suggestions = []
        
        # Architecture pattern detection with validated components
        patterns = {
            "web_frontend": {
                "keywords": ["react", "frontend", "web app", "spa", "angular", "vue", "static"],
                "components": ["AppServices", "ContainerApps", "FrontDoors"]
            },
            "api_backend": {
                "keywords": ["backend", "api", "rest", "nodejs", "python", "fastapi", "express"],
                "components": ["AppServices", "ContainerApps", "FunctionApps"]
            },
            "database": {
                "keywords": ["database", "db", "postgresql", "postgres", "mysql", "sql"],
                "components": ["DatabaseForPostgresqlServers", "DatabaseForMysqlServers", "SQLDatabases"]
            },
            "nosql": {
                "keywords": ["mongodb", "nosql", "cosmos", "document", "json"],
                "components": ["CosmosDb"]
            },
            "cache": {
                "keywords": ["cache", "redis", "caching", "session"],
                "components": ["CacheForRedis"]
            },
            "storage": {
                "keywords": ["storage", "blob", "file", "images", "documents", "assets"],
                "components": ["BlobStorage", "StorageAccounts"]
            },
            "container": {
                "keywords": ["docker", "container", "kubernetes", "k8s"],
                "components": ["ContainerApps", "ContainerInstances", "KubernetesServices"]
            },
            "messaging": {
                "keywords": ["queue", "message", "event", "notification"],
                "components": ["ServiceBus", "EventHubs"]
            },
            "auth": {
                "keywords": ["auth", "authentication", "login", "security", "identity"],
                "components": ["KeyVaults", "ActiveDirectory"]
            }
        }
        
        detected_components = []
        imports_needed = set()
        
        for pattern_name, pattern_info in patterns.items():
            if any(keyword in description_lower for keyword in pattern_info["keywords"]):
                for comp_name in pattern_info["components"]:
                    validation = self.validate_component(comp_name)
                    if validation["valid"]:
                        detected_components.append({
                            "id": pattern_name,
                            "canonical": validation["canonical"],
                            "submodule": validation["submodule"],
                            "class": validation["class"],
                            "label": self._generate_label(pattern_name, comp_name),
                            "pattern": pattern_name
                        })
                        imports_needed.add(validation["submodule"])
        
        # Remove duplicates
        unique_components = []
        seen_canonicals = set()
        for comp in detected_components:
            if comp["canonical"] not in seen_canonicals:
                seen_canonicals.add(comp["canonical"])
                unique_components.append(comp)
        
        return {
            "components": unique_components,
            "imports_needed": sorted(imports_needed),
            "validation_passed": True,
            "description_analyzed": description[:100] + "..." if len(description) > 100 else description
        }
    
    def _generate_label(self, pattern: str, component: str) -> str:
        """Generate human-readable labels for components"""
        labels = {
            "web_frontend": "Web Frontend",
            "api_backend": "Backend API", 
            "database": "Database",
            "nosql": "NoSQL Database",
            "cache": "Cache",
            "storage": "Storage",
            "container": "Container Service",
            "messaging": "Messaging",
            "auth": "Authentication"
        }
        return labels.get(pattern, pattern.replace("_", " ").title())
    
    def generate_validated_diagram_code(self, components: List[Dict], 
                                      description: str = "Architecture Diagram") -> str:
        """Generate diagram code with validated components and proper imports"""
        
        # Group imports by submodule
        imports_by_module = {}
        for comp in components:
            submodule = comp["submodule"]
            if submodule not in imports_by_module:
                imports_by_module[submodule] = []
            imports_by_module[submodule].append(comp["canonical"])
        
        # Generate import statements
        imports = ["from diagrams import Diagram, Edge"]
        for submodule in sorted(imports_by_module.keys()):
            components_list = ", ".join(sorted(set(imports_by_module[submodule])))
            imports.append(f"from diagrams.azure.{submodule} import {components_list}")
        
        # Generate diagram code
        code_lines = imports + [""]
        code_lines.append(f'with Diagram("{description[:50]}...", show=False, direction="TB"):')
        
        # Add component declarations
        for comp in components:
            comp_id = comp["id"]
            canonical = comp["canonical"] 
            label = comp["label"]
            code_lines.append(f'    {comp_id} = {canonical}("{label}")')
        
        # Add basic connections (can be enhanced)
        if len(components) >= 2:
            code_lines.append("")
            code_lines.append("    # Connections")
            for i in range(len(components) - 1):
                curr_id = components[i]["id"]
                next_id = components[i + 1]["id"]
                code_lines.append(f"    {curr_id} >> {next_id}")
        
        return "\n".join(code_lines)

# Validation Tool Functions for MCP Integration
def validate_component_names(names: List[str]) -> Dict[str, Any]:
    """MCP tool function for validating component names"""
    validator = AzureComponentValidator()
    results = {}
    
    for name in names:
        results[name] = validator.validate_component(name)
    
    return {
        "validation_results": results,
        "total_checked": len(names),
        "valid_count": sum(1 for r in results.values() if r["valid"]),
        "invalid_count": sum(1 for r in results.values() if not r["valid"])
    }

def suggest_architecture_components(description: str, provider: str = "azure") -> Dict[str, Any]:
    """MCP tool function for suggesting architecture components"""
    validator = AzureComponentValidator()
    return validator.suggest_components_for_architecture(description, provider)

def generate_validated_diagram(description: str, provider: str = "azure") -> Dict[str, Any]:
    """MCP tool function that combines suggestion and code generation"""
    validator = AzureComponentValidator()
    
    # Get component suggestions
    suggestions = validator.suggest_components_for_architecture(description, provider)
    
    if not suggestions["components"]:
        return {
            "success": False,
            "error": "No suitable components found for the given description",
            "description": description
        }
    
    # Generate validated code
    diagram_code = validator.generate_validated_diagram_code(
        suggestions["components"], 
        description
    )
    
    return {
        "success": True,
        "diagram_code": diagram_code,
        "components_used": suggestions["components"],
        "imports_needed": suggestions["imports_needed"],
        "validation_passed": True,
        "description_analyzed": suggestions["description_analyzed"]
    }

if __name__ == "__main__":
    # Example usage
    validator = AzureComponentValidator()
    
    # Test validation
    print("=== Component Validation ===")
    test_names = ["AppServices", "ACR", "StaticWebApps", "InvalidComponent"]
    for name in test_names:
        result = validator.validate_component(name)
        print(f"{name}: {result}")
    
    print("\n=== Architecture Suggestion ===")
    description = "A web application with React frontend, Node.js backend, PostgreSQL database, and Redis cache"
    suggestions = validator.suggest_components_for_architecture(description)
    print(f"Suggestions: {suggestions}")
    
    print("\n=== Generated Code ===")
    validated_result = generate_validated_diagram(description)
    if validated_result["success"]:
        print(validated_result["diagram_code"])
