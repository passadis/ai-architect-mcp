// API Configuration
// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE_URL = ''
const APP_ENV = import.meta.env.VITE_APP_ENV || 'development';

// API Endpoints
export const API_ENDPOINTS = {
  GENERATE_ARCHITECTURE: `${API_BASE_URL}/api/generate-architecture`,
  CHECK_ARCHITECTURE_EXISTS: `${API_BASE_URL}/api/check-architecture-exists`,
  SAVE_ARCHITECTURE: `${API_BASE_URL}/api/save-architecture`,
  SAVED_ARCHITECTURES: `${API_BASE_URL}/api/saved-architectures`,
  DELETE_ARCHITECTURE: (id) => `${API_BASE_URL}/api/saved-architectures/${id}`,
  LOAD_ARCHITECTURE: (id) => `${API_BASE_URL}/api/saved-architectures/${id}`,
  EXPORT_DIAGRAM: (diagramUrl, filename) => 
    `${API_BASE_URL}/api/export/diagram${diagramUrl}?filename=${encodeURIComponent(filename)}`,
  DIAGRAM_URL: (diagramPath) => `${API_BASE_URL}${diagramPath}`,
  
  // ==================== VALIDATION ENDPOINTS ====================
  VALIDATE_COMPONENTS: `${API_BASE_URL}/api/validate-components`,
  SUGGEST_ARCHITECTURE: `${API_BASE_URL}/api/suggest-architecture`, 
  GENERATE_VALIDATED_DIAGRAM: `${API_BASE_URL}/api/generate-validated-diagram`,
};

// Configuration
export const CONFIG = {
  API_BASE_URL,
  APP_ENV,
  IS_DEVELOPMENT: APP_ENV === 'development',
  IS_PRODUCTION: APP_ENV === 'production',
};

export default CONFIG;
