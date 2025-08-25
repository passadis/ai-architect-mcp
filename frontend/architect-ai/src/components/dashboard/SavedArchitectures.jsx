import React, { useState, useEffect } from 'react';
import { Clock, FileText, LayoutTemplate, ExternalLink, Trash2 } from 'lucide-react';

const SavedArchitectures = ({ onSelectArchitecture }) => {
  const [savedItems, setSavedItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSavedArchitectures();
  }, []);

  const fetchSavedArchitectures = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // For demo purposes, we'll simulate an API call with a timeout
      // In a real implementation, this would be a fetch to your Azure Function
      setTimeout(() => {
        // Mock data
        const mockSavedItems = [
          {
            id: 'arch-001',
            title: 'E-commerce Microservice Architecture',
            timestamp: '2025-03-07T14:30:00Z',
            preview: 'Microservices for user auth, product catalog, orders, and payments'
          },
          {
            id: 'arch-002',
            title: 'Data Warehouse Solution',
            timestamp: '2025-03-05T09:15:00Z',
            preview: 'Data warehouse with ETL pipelines and reporting services'
          },
          {
            id: 'arch-003',
            title: 'IoT Platform Architecture',
            timestamp: '2025-03-01T16:45:00Z',
            preview: 'IoT device management with real-time data processing'
          }
        ];
        
        setSavedItems(mockSavedItems);
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      console.error('Error fetching saved architectures:', err);
      setError('Failed to load saved architectures. Please try again.');
      setIsLoading(false);
    }
  };

  const handleSelect = (item) => {
    if (onSelectArchitecture) {
      onSelectArchitecture(item);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation(); // Prevent triggering the parent click
    
    if (window.confirm('Are you sure you want to delete this architecture?')) {
      // In a real implementation, this would call your API
      setSavedItems(savedItems.filter(item => item.id !== id));
      // Show a temporary success message
      // You could add state for this and display it in the UI
    }
  };

  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Saved Architectures</h2>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Saved Architectures</h2>
        <div className="bg-red-50 text-red-700 p-4 rounded-md">
          <p>{error}</p>
          <button 
            onClick={fetchSavedArchitectures}
            className="mt-2 text-sm font-medium text-red-700 hover:text-red-900"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-gray-900">Saved Architectures</h2>
        <button 
          onClick={fetchSavedArchitectures}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Refresh
        </button>
      </div>
      
      {savedItems.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-2" />
          <p>No saved architectures yet.</p>
          <p className="text-sm mt-1">Create and save a design to see it here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {savedItems.map(item => (
            <div 
              key={item.id}
              onClick={() => handleSelect(item)}
              className="border border-gray-200 rounded-md p-4 hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex justify-between">
                <h3 className="font-medium text-gray-900">{item.title}</h3>
                <div className="flex items-center text-gray-500 text-sm">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatDate(item.timestamp)}
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-1">{item.preview}</p>
              <div className="flex justify-between mt-3">
                <div className="flex space-x-4">
                  <button className="text-xs text-blue-600 hover:text-blue-800 flex items-center">
                    <FileText className="h-3 w-3 mr-1" />
                    Document
                  </button>
                  <button className="text-xs text-blue-600 hover:text-blue-800 flex items-center">
                    <LayoutTemplate className="h-3 w-3 mr-1" />
                    Diagram
                  </button>
                </div>
                <button 
                  onClick={(e) => handleDelete(item.id, e)}
                  className="text-xs text-red-600 hover:text-red-800 flex items-center"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedArchitectures;