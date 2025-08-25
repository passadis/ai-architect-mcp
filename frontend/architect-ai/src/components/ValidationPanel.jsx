import React, { useState, useEffect } from 'react';
import { validateTextComponents, getArchitectureSuggestions } from '../services/validationService.js';

const ValidationPanel = ({ description, onValidationChange }) => {
  const [validationResults, setValidationResults] = useState({});
  const [suggestions, setSuggestions] = useState([]);
  const [isValidating, setIsValidating] = useState(false);
  const [detectedComponents, setDetectedComponents] = useState([]);

  useEffect(() => {
    const validateDescription = async () => {
      if (!description || description.length < 10) return;

      setIsValidating(true);
      
      try {
        // Validate detected components
        const componentValidation = await validateTextComponents(description);
        setValidationResults(componentValidation.validationResults || {});
        setDetectedComponents(componentValidation.detectedComponents || []);

        // Get architecture suggestions
        const archSuggestions = await getArchitectureSuggestions(description);
        setSuggestions(archSuggestions.suggestions.slice(0, 5) || []); // Show top 5

        // Notify parent component
        if (onValidationChange) {
          onValidationChange({
            validationResults: componentValidation.validationResults,
            suggestions: archSuggestions.suggestions,
            hasErrors: Object.values(componentValidation.validationResults || {}).some(r => !r.valid)
          });
        }
      } catch (error) {
        console.error('Validation error:', error);
      } finally {
        setIsValidating(false);
      }
    };

    const debounceTimer = setTimeout(validateDescription, 1000);
    return () => clearTimeout(debounceTimer);
  }, [description, onValidationChange]);

  const getValidationIcon = (isValid) => {
    return isValid ? (
      <span className="text-green-500 text-sm">✅</span>
    ) : (
      <span className="text-red-500 text-sm">❌</span>
    );
  };

  if (!description || description.length < 10) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
        <div className="text-gray-500 text-sm">
          💡 Start typing your architecture description to see real-time validation and suggestions...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm mt-4">
      {/* Header */}
      <div className="bg-blue-50 px-4 py-3 border-b border-gray-200 rounded-t-lg">
        <h3 className="font-semibold text-gray-800 flex items-center">
          🎯 Real-time Validation
          {isValidating && (
            <span className="ml-2 text-blue-500 text-sm animate-pulse">Validating...</span>
          )}
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Detected Components */}
        {detectedComponents.length > 0 && (
          <div>
            <h4 className="font-medium text-gray-700 mb-2">📦 Detected Azure Components:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {detectedComponents.map((component) => {
                const validation = validationResults[component];
                const isValid = validation?.valid || false;
                const canonical = validation?.canonical || component;
                const submodule = validation?.submodule || 'unknown';
                
                return (
                  <div
                    key={component}
                    className={`flex items-center justify-between p-2 rounded border ${
                      isValid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      {getValidationIcon(isValid)}
                      <span className="font-mono text-sm">{canonical}</span>
                      {isValid && (
                        <span className="text-xs text-gray-500">({submodule})</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Architecture Suggestions */}
        {suggestions.length > 0 && (
          <div>
            <h4 className="font-medium text-gray-700 mb-2">💡 Smart Suggestions:</h4>
            <div className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded"
                >
                  <div>
                    <div className="font-medium text-blue-800">
                      {suggestion.component || 'Unknown Component'}
                    </div>
                    <div className="text-sm text-blue-600">
                      {suggestion.usage || 'Suggested usage'} • from {suggestion.submodule || 'azure'}
                    </div>
                  </div>
                  <button
                    className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                    onClick={() => {
                      // Add to description or copy to clipboard
                      navigator.clipboard.writeText(suggestion.component);
                    }}
                  >
                    Use
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Validation Summary */}
        {Object.keys(validationResults).length > 0 && (
          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                {Object.values(validationResults).filter(r => r.valid).length} valid • {' '}
                {Object.values(validationResults).filter(r => !r.valid).length} invalid
              </span>
              <span className="text-blue-600 font-medium">
                Ready for enhanced generation 🚀
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ValidationPanel;
