// Enhanced Validation Service
import { API_ENDPOINTS } from '../config/api.js';

/**
 * Validate Azure component names in real-time
 * @param {string[]} componentNames - Array of component names to validate
 * @returns {Promise<Object>} Validation results with valid/invalid components
 */
export const validateAzureComponents = async (componentNames) => {
  try {
    const response = await fetch(API_ENDPOINTS.VALIDATE_COMPONENTS, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        component_names: componentNames
      }),
    });

    if (!response.ok) {
      throw new Error(`Validation failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      validationResults: data.validation_results || {},
      error: data.error || null
    };
  } catch (error) {
    console.error('Component validation error:', error);
    return {
      success: false,
      validationResults: {},
      error: error.message
    };
  }
};

/**
 * Get architecture component suggestions based on description
 * @param {string} description - Architecture description
 * @param {string[]} architectureTypes - Types of components to suggest
 * @returns {Promise<Object>} Architecture suggestions
 */
export const getArchitectureSuggestions = async (description, architectureTypes = ['frontend', 'backend', 'database', 'cache']) => {
  try {
    const response = await fetch(API_ENDPOINTS.SUGGEST_ARCHITECTURE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description,
        architecture_types: architectureTypes
      }),
    });

    if (!response.ok) {
      throw new Error(`Architecture suggestion failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      suggestions: data.suggestions || [],
      importsNeeded: data.imports_needed || [],
      error: data.error || null
    };
  } catch (error) {
    console.error('Architecture suggestion error:', error);
    return {
      success: false,
      suggestions: [],
      importsNeeded: [],
      error: error.message
    };
  }
};

/**
 * Generate diagram with full validation
 * @param {string} description - Architecture description
 * @param {string} provider - Cloud provider (default: azure)
 * @param {boolean} includeValidation - Whether to include validation
 * @returns {Promise<Object>} Validated diagram generation result
 */
export const generateValidatedDiagram = async (description, provider = 'azure', includeValidation = true) => {
  try {
    const response = await fetch(API_ENDPOINTS.GENERATE_VALIDATED_DIAGRAM, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description,
        provider,
        include_validation: includeValidation
      }),
    });

    if (!response.ok) {
      throw new Error(`Validated diagram generation failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: data.success || false,
      validationPassed: data.validation_passed || false,
      componentsUsed: data.components_used || [],
      diagramCode: data.diagram_code || '',
      validationErrors: data.validation_errors || [],
      diagramPath: data.diagram_path || null,
      error: data.error || null
    };
  } catch (error) {
    console.error('Validated diagram generation error:', error);
    return {
      success: false,
      validationPassed: false,
      componentsUsed: [],
      diagramCode: '',
      validationErrors: [error.message],
      diagramPath: null,
      error: error.message
    };
  }
};

/**
 * Real-time component validation as user types
 * @param {string} text - Text to extract potential component names from
 * @returns {Promise<Object>} Validation results for detected components
 */
export const validateTextComponents = async (text) => {
  // Extract potential Azure component names from text
  const azureKeywords = [
    'AppServices', 'ContainerApps', 'ACR', 'AKS', 'FunctionApps',
    'SQLDatabases', 'CosmosDb', 'CacheForRedis', 'BlobStorage',
    'KeyVaults', 'StaticWebApps', 'ApplicationGateway', 'LoadBalancer'
  ];
  
  const detectedComponents = azureKeywords.filter(keyword => 
    text.toLowerCase().includes(keyword.toLowerCase())
  );
  
  if (detectedComponents.length === 0) {
    return { success: true, validationResults: {}, detectedComponents: [] };
  }
  
  const validation = await validateAzureComponents(detectedComponents);
  return {
    ...validation,
    detectedComponents
  };
};

export default {
  validateAzureComponents,
  getArchitectureSuggestions,
  generateValidatedDiagram,
  validateTextComponents
};
