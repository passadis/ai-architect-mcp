import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  FileText, 
  LayoutTemplate, 
  ArrowLeft, 
  Send, 
  RefreshCw, 
  Download, 
  AlertCircle, 
  CheckCircle, 
  Save,
  Clock,
  Trash2,
  Copy
} from 'lucide-react';
import { API_ENDPOINTS } from '../config/api.js';
import ValidationPanel from '../components/ValidationPanel.jsx';

const DashboardPage = () => {
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('document');
  const [hasResults, setHasResults] = useState(false);
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [savedArchitectures, setSavedArchitectures] = useState([]);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [showSavedDropdown, setShowSavedDropdown] = useState(false);
  const [architectureExists, setArchitectureExists] = useState(null); // null, false, or architecture object
  const [exportStatus, setExportStatus] = useState(null); // { type: 'success'|'error', message: string }
  const [isExporting, setIsExporting] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('');
  const [validationState, setValidationState] = useState({
    validationResults: {},
    suggestions: [],
    hasErrors: false
  });

  const [designDocument, setDesignDocument] = useState('');
  const [diagramUrl, setDiagramUrl] = useState('');

  // Load saved architectures on component mount
  useEffect(() => {
    loadSavedArchitectures();
  }, []);

  // Auto-dismiss toast after 5 seconds
  useEffect(() => {
    if (exportStatus) {
      const timer = setTimeout(() => {
        setExportStatus(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [exportStatus]);

  // Check if architecture exists
  const checkArchitectureExists = async (designDoc) => {
    if (!designDoc || designDoc.trim() === '') {
      setArchitectureExists(null);
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.CHECK_ARCHITECTURE_EXISTS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          design_document: designDoc
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setArchitectureExists(result.exists ? result.architecture : false);
      } else {
        setArchitectureExists(null);
      }
    } catch (error) {
      console.error('Error checking architecture exists:', error);
      setArchitectureExists(null);
    }
  };

  const loadSavedArchitectures = async () => {
    try {
      setIsLoadingSaved(true);
      const response = await fetch(API_ENDPOINTS.SAVED_ARCHITECTURES);
      
      if (!response.ok) {
        throw new Error('Failed to load saved architectures');
      }
      
      const data = await response.json();
      // Handle both possible response formats
      const architectures = data.architectures || data || [];
      setSavedArchitectures(architectures);
      
    } catch (error) {
      console.error('Error loading saved architectures:', error);
      setSavedArchitectures([]);
    } finally {
      setIsLoadingSaved(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setIsProcessing(true);
    setHasResults(false);
    setDesignDocument('');
    setDiagramUrl('');
    setError('');
    setArchitectureExists(null); // Reset architecture exists state
    setProcessingMessage('🔄 Analyzing your requirements...');

    try {
      setProcessingMessage('🧠 Generating architecture design...');
      const response = await fetch(API_ENDPOINTS.GENERATE_ARCHITECTURE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      setProcessingMessage('🎨 Creating visual diagram...');
      const data = await response.json();
      console.log('API Response:', data);
      
      setDesignDocument(data.design_document || 'No design document generated');
      setDiagramUrl(data.diagram_url || '');
      setHasResults(true);
      setProcessingMessage('');
      
      // Check if this architecture already exists after setting the design document
      if (data.design_document) {
        await checkArchitectureExists(data.design_document);
      }
      
    } catch (error) {
      console.error('Error generating architecture:', error);
      setError(error.message || 'Something went wrong. Please try again.');
      setProcessingMessage('');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveArchitecture = async () => {
    if (!designDocument || !hasResults) return;

    setIsSaving(true);
    try {
      const title = generateTitle(designDocument) || 'Generated Architecture';
      const preview = generatePreview(designDocument) || 'Architecture design document';

      const response = await fetch(API_ENDPOINTS.SAVE_ARCHITECTURE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          preview,
          design_document: designDocument,
          diagram_url: diagramUrl || ''
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to save architecture');
      }

      const result = await response.json();
      
      if (result.already_exists) {
        alert('This architecture already exists in your saved collection!');
      } else {
        alert('Architecture saved successfully!');
      }
      
      console.log('Saved architecture:', result);
      
      // Update the architectureExists state to reflect the save
      setArchitectureExists(result.saved_item);
      
      // Reload saved architectures
      await loadSavedArchitectures();
      
    } catch (error) {
      console.error('Error saving architecture:', error);
      alert(`Failed to save architecture: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoadArchitecture = async (architecture) => {
    try {
      // If we only have an ID, fetch the full architecture
      if (typeof architecture === 'string' || (architecture.id && !architecture.design_document)) {
        const archId = typeof architecture === 'string' ? architecture : architecture.id;
        const response = await fetch(API_ENDPOINTS.LOAD_ARCHITECTURE(archId));
        
        if (!response.ok) {
          throw new Error('Failed to load architecture');
        }
        
        architecture = await response.json();
      }
      
      setDesignDocument(architecture.design_document || '');
      setDiagramUrl(architecture.diagram_url || '');
      setInput(''); // Clear input since we're loading saved content
      setHasResults(true);
      setError('');
      setShowSavedDropdown(false);
      setArchitectureExists(architecture); // Mark this architecture as already saved
      
      console.log('Loaded architecture:', architecture);
    } catch (error) {
      console.error('Error loading architecture:', error);
      setError(`Failed to load architecture: ${error.message}`);
    }
  };

  const handleDeleteArchitecture = async (archId, event) => {
    event.stopPropagation(); // Prevent triggering load
    
    if (!confirm('Are you sure you want to delete this architecture?')) {
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.DELETE_ARCHITECTURE(archId), {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete architecture');
      }

      alert('Architecture deleted successfully!');
      await loadSavedArchitectures();
      
    } catch (error) {
      console.error('Error deleting architecture:', error);
      alert(`Failed to delete architecture: ${error.message}`);
    }
  };

  // Export functions
  const exportDesignDocument = () => {
    if (!designDocument) {
      setExportStatus({ type: 'error', message: 'No design document to export' });
      return;
    }

    try {
      // Generate title for filename
      const title = generateTitle(designDocument) || 'Architecture_Design_Document';
      const filename = `${title.replace(/[^a-zA-Z0-9_-]/g, '_')}.md`;

      // Create blob and download
      const blob = new Blob([designDocument], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setExportStatus({ type: 'success', message: `Design document exported as ${filename}` });
      
    } catch (error) {
      console.error('Error exporting document:', error);
      setExportStatus({ type: 'error', message: 'Failed to export design document' });
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setExportStatus({ type: 'success', message: 'Copied to clipboard!' });
    } catch (error) {
      console.error('Failed to copy:', error);
      setExportStatus({ type: 'error', message: 'Failed to copy to clipboard' });
    }
  };

  const exportDiagramPNG = async () => {
    if (!diagramUrl) {
      setExportStatus({ type: 'error', message: 'No diagram to export' });
      return;
    }

    setIsExporting(true);
    try {
      // Generate filename
      const title = generateTitle(designDocument) || 'Architecture_Diagram';
      const filename = `${title.replace(/[^a-zA-Z0-9_-]/g, '_')}.png`;

      // Check if diagramUrl is an Azure Blob URL (starts with https://)
      if (diagramUrl.startsWith('https://')) {
        // Direct download from Azure Blob Storage
        const response = await fetch(diagramUrl);
        if (!response.ok) {
          throw new Error('Failed to fetch diagram from Azure Storage');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        // Create download link
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Clean up
        window.URL.revokeObjectURL(url);
      } else {
        // Fallback to the export endpoint for local files
        const exportUrl = API_ENDPOINTS.EXPORT_DIAGRAM(diagramUrl, filename);
        
        // Create download link
        const a = document.createElement('a');
        a.href = exportUrl;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
      
      setExportStatus({ type: 'success', message: `Diagram exported as ${filename}` });
      
    } catch (error) {
      console.error('Error exporting diagram:', error);
      setExportStatus({ type: 'error', message: 'Failed to export diagram' });
      
      // Fallback: open image in new tab for manual save
      try {
        const fullImageUrl = API_ENDPOINTS.DIAGRAM_URL(diagramUrl);
        const newWindow = window.open(fullImageUrl, '_blank');
        if (newWindow) {
          setExportStatus({ type: 'error', message: 'Image opened in new tab. Right-click to save manually.' });
        } else {
          throw new Error('Popup blocked');
        }
      } catch (fallbackError) {
        console.error('Fallback method also failed:', fallbackError);
        setExportStatus({ type: 'error', message: 'Export failed. Right-click on the diagram and select "Save image as..."' });
      }
    } finally {
      setIsExporting(false);
    }
  };

  const generateTitle = (document) => {
    if (!document) return '';
    
    const lines = document.split('\n').filter(line => line.trim());
    for (const line of lines) {
      if (line.startsWith('# ')) {
        return line.substring(2).trim();
      } else if (line.startsWith('## ')) {
        return line.substring(3).trim();
      }
    }
    
    const firstLine = lines[0]?.trim();
    if (firstLine && firstLine.length > 10) {
      return firstLine.length > 50 ? firstLine.substring(0, 47) + '...' : firstLine;
    }
    
    return 'Generated Architecture';
  };

  const generatePreview = (document) => {
    if (!document) return '';
    
    const plainText = document
      .replace(/^#+\s*/gm, '')
      .replace(/^\s*[-*]\s*/gm, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .trim();
    
    const sentences = plainText.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const preview = sentences.slice(0, 2).join('. ');
    
    return preview.length > 150 ? preview.substring(0, 147) + '...' : preview;
  };

  const renderDocument = (text) => {
    if (!text) return <p className="text-gray-500">No content available</p>;
    
    const lines = text.split('\n');
    const elements = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.startsWith('# ')) {
        elements.push(<h1 key={i} className="text-2xl font-bold text-gray-900 mt-6 mb-3">{line.substring(2)}</h1>);
      } else if (line.startsWith('## ')) {
        elements.push(<h2 key={i} className="text-xl font-semibold text-gray-800 mt-5 mb-2">{line.substring(3)}</h2>);
      } else if (line.startsWith('### ')) {
        elements.push(<h3 key={i} className="text-lg font-medium text-gray-700 mt-4 mb-2">{line.substring(4)}</h3>);
      } else if (line.startsWith('- ')) {
        elements.push(<li key={i} className="ml-4 text-gray-700 list-disc">{line.substring(2)}</li>);
      } else if (line.startsWith('* ')) {
        elements.push(<li key={i} className="ml-4 text-gray-700 list-disc">{line.substring(2)}</li>);
      } else if (line.trim() === '') {
        elements.push(<br key={i} />);
      } else if (line.trim()) {
        elements.push(<p key={i} className="text-gray-700 mb-2">{line}</p>);
      }
    }
    
    return <div className="prose max-w-none">{elements}</div>;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <img src="/mainlogo.png" alt="ArchitectAI Logo" className="h-14 w-auto" />
          </div>
          <div className="flex items-center space-x-4">
            {/* Saved Architectures Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowSavedDropdown(!showSavedDropdown)}
                  className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
                  disabled={isLoadingSaved}
                >
                  {isLoadingSaved ? (
                    <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <FileText className="h-4 w-4 mr-1" />
                  )}
                  Saved Architectures ({savedArchitectures.length})
                </button>
                
                {showSavedDropdown && (
                  <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-10 max-h-96 overflow-y-auto">
                    {savedArchitectures.length === 0 ? (
                      <div className="p-4 text-gray-500 text-center">
                        No saved architectures yet
                      </div>
                    ) : (
                      savedArchitectures.map((arch) => (
                        <div 
                          key={arch.id} 
                          className="p-3 hover:bg-gray-50 border-b border-gray-100 cursor-pointer flex justify-between items-start"
                          onClick={() => handleLoadArchitecture(arch)}
                        >
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900 text-sm">{arch.title}</h4>
                            <p className="text-xs text-gray-500 mt-1">{arch.preview}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              <Clock className="h-3 w-3 inline mr-1" />
                              {new Date(arch.timestamp).toLocaleDateString()}
                            </p>
                          </div>
                          <button
                            onClick={(e) => handleDeleteArchitecture(arch.id, e)}
                            className="ml-2 p-1 text-gray-400 hover:text-red-600"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
              
              <a 
                href="/"
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Home
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-grow flex flex-col lg:flex-row">
        {/* Input Section */}
        <div className="w-full lg:w-1/2 p-4 bg-white border-r">
          <div className="max-w-2xl mx-auto p-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Describe Your Architecture</h2>
            <p className="text-gray-600 mb-6">
              Tell us about your architectural needs in plain language. Our AI agents will collaborate to generate design documents and diagrams for you.
            </p>
            
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <textarea
                  className="w-full h-64 px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Example: Design a scalable e-commerce platform using Azure services. Include user authentication, product catalog, shopping cart, order processing, payment integration, and inventory management. The system should handle 10,000 concurrent users and process 1,000 orders per hour."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isProcessing}
                  maxLength={2000}
                />
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-gray-500">
                    Be specific about your requirements, expected scale, and preferred Azure services
                  </span>
                  <span className={`text-xs ${input.length > 1800 ? 'text-red-500' : 'text-gray-400'}`}>
                    {input.length}/2000
                  </span>
                </div>
              </div>
              
              {/* Enhanced Validation Panel */}
              <ValidationPanel 
                description={input}
                onValidationChange={setValidationState}
              />
              
              <button
                type="submit"
                disabled={isProcessing || !input.trim()}
                className={`w-full flex justify-center items-center px-4 py-2 rounded-md text-white font-medium transition-colors ${
                  isProcessing || !input.trim() ? 'bg-gray-400 cursor-not-allowed' : 
                  validationState.hasErrors ? 'bg-orange-600 hover:bg-orange-700' :
                  'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="animate-spin h-5 w-5 mr-2" />
                    {processingMessage || 'Processing...'}
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    {validationState.hasErrors ? 'Generate (with warnings)' : 'Generate Architecture'}
                  </>
                )}
              </button>
            </form>

            {!hasResults && input.length === 0 && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="text-sm font-medium text-blue-900 mb-2">💡 Tips for better results:</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Be specific about your technology stack and requirements</li>
                  <li>• Include expected user load and performance needs</li>
                  <li>• Mention security, compliance, or integration requirements</li>
                  <li>• Describe your data storage and processing needs</li>
                </ul>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Processing Status */}
            {isProcessing && (
              <div className="mt-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">AI Agents Working...</h3>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Design Agent</p>
                      <p className="text-sm text-gray-500">Generating architecture document...</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Diagram Agent</p>
                      <p className="text-sm text-gray-500">Creating visual diagram...</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Success Status */}
            {hasResults && !isProcessing && (
              <div className="mt-8">
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-green-600">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    <span className="text-sm font-medium">Architecture generated successfully!</span>
                    {architectureExists && (
                      <span className="ml-2 text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded">
                        Already saved
                      </span>
                    )}
                  </div>
                  <button
                    onClick={handleSaveArchitecture}
                    disabled={isSaving || architectureExists}
                    className={`flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                      architectureExists 
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                        : isSaving 
                          ? 'bg-gray-400 text-white cursor-not-allowed' 
                          : 'bg-green-600 hover:bg-green-700 text-white'
                    }`}
                    title={architectureExists ? `Already saved on ${new Date(architectureExists.timestamp).toLocaleDateString()}` : ''}
                  >
                    {isSaving ? (
                      <>
                        <RefreshCw className="animate-spin h-4 w-4 mr-1" />
                        Saving...
                      </>
                    ) : architectureExists ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Saved
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-1" />
                        Save
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Output Section */}
        <div className="w-full lg:w-1/2 p-4 bg-gray-50">
          <div className="max-w-4xl mx-auto p-4">
            <div className="flex border-b border-gray-200">
              <button
                className={`py-2 px-4 font-medium transition-colors ${
                  activeTab === 'document' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'
                }`}
                onClick={() => setActiveTab('document')}
              >
                Design Document
              </button>
              <button
                className={`py-2 px-4 font-medium transition-colors ${
                  activeTab === 'diagram' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'
                }`}
                onClick={() => setActiveTab('diagram')}
              >
                Architecture Diagram
              </button>
            </div>

            <div className="mt-6">
              {!hasResults ? (
                <div className="text-center py-16">
                  <div className="mx-auto h-16 w-16 text-gray-400">
                    {activeTab === 'document' ? <FileText className="h-16 w-16" /> : <LayoutTemplate className="h-16 w-16" />}
                  </div>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Describe your architecture requirements to generate content or load a saved architecture.
                  </p>
                </div>
              ) : (
                <>
                  {activeTab === 'document' ? (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-medium text-gray-900">Design Document</h3>
                        <div className="flex space-x-3">
                          <button 
                            onClick={() => copyToClipboard(designDocument)}
                            disabled={!designDocument}
                            className={`flex items-center transition-colors ${
                              designDocument 
                                ? 'text-blue-600 hover:text-blue-800' 
                                : 'text-gray-400 cursor-not-allowed'
                            }`}
                          >
                            <Copy className="h-4 w-4 mr-1" />
                            Copy
                          </button>
                          <button 
                            onClick={exportDesignDocument}
                            disabled={!designDocument}
                            className={`flex items-center transition-colors ${
                              designDocument 
                                ? 'text-blue-600 hover:text-blue-800' 
                                : 'text-gray-400 cursor-not-allowed'
                            }`}
                          >
                            <Download className="h-4 w-4 mr-1" />
                            Export
                          </button>
                        </div>
                      </div>
                      <div className="max-h-96 overflow-y-auto">
                        {renderDocument(designDocument)}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-medium text-gray-900">Architecture Diagram</h3>
                        <button 
                          onClick={exportDiagramPNG}
                          disabled={!diagramUrl || isExporting}
                          className={`flex items-center transition-colors ${
                            diagramUrl && !isExporting
                              ? 'text-blue-600 hover:text-blue-800' 
                              : 'text-gray-400 cursor-not-allowed'
                          }`}
                        >
                          {isExporting ? (
                            <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4 mr-1" />
                          )}
                          {isExporting ? 'Exporting...' : 'Export'}
                        </button>
                      </div>
                      <div className="border border-gray-200 rounded bg-white flex items-center justify-center p-4 min-h-[400px]">
                        {diagramUrl ? (
                          <img 
                            src={API_ENDPOINTS.DIAGRAM_URL(diagramUrl)} 
                            alt="Architecture Diagram" 
                            className="max-h-96 w-auto object-contain"
                            onError={(e) => {
                              console.error('Image failed to load:', e.target.src);
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'block';
                            }}
                          />
                        ) : null}
                        <div 
                          className="text-gray-500 text-center"
                          style={{ display: diagramUrl ? 'none' : 'block' }}
                        >
                          {hasResults ? 'Diagram not available or failed to load' : 'Diagram not generated yet'}
                        </div>
                      </div>
                      {diagramUrl && (
                        <div className="mt-4 text-sm text-gray-500">
                          <p>
                            This diagram illustrates the architecture based on your requirements. 
                            Each component represents a service or system in your architecture.
                          </p>
                          <p className="mt-1 text-xs">Image URL: {diagramUrl}</p>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            &copy; 2025 ArchitectAI. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Toast Notification */}
      {exportStatus && (
        <div className={`fixed bottom-4 right-4 p-4 rounded-lg shadow-lg max-w-sm z-50 transition-all duration-300 ${
          exportStatus.type === 'success' 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : 'bg-red-100 text-red-800 border border-red-200'
        }`}>
          <div className="flex items-center">
            {exportStatus.type === 'success' ? (
              <CheckCircle className="h-5 w-5 mr-2 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
            )}
            <span className="text-sm">{exportStatus.message}</span>
            <button
              onClick={() => setExportStatus(null)}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;