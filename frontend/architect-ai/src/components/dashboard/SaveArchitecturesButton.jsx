import React, { useState } from 'react';
import { FolderOpen, X } from 'lucide-react';
import SavedArchitectures from './SavedArchitectures';

const SavedArchitecturesButton = ({ onSelectArchitecture }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const togglePanel = () => {
    setIsOpen(!isOpen);
  };
  
  const handleSelectArchitecture = (architecture) => {
    if (onSelectArchitecture) {
      onSelectArchitecture(architecture);
    }
    setIsOpen(false); // Close panel after selection
  };
  
  return (
    <>
      {/* Button to open saved architectures */}
      <button 
        onClick={togglePanel}
        className="flex items-center text-gray-600 hover:text-gray-900 mr-4"
      >
        <FolderOpen className="h-5 w-5 mr-1" />
        My Architectures
      </button>
      
      {/* Slide-out panel for saved architectures */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div className="absolute inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={togglePanel}></div>
          
          <div className="fixed inset-y-0 right-0 max-w-full flex">
            <div className="relative w-screen max-w-md">
              <div className="h-full flex flex-col bg-white shadow-xl overflow-y-auto">
                {/* Panel header */}
                <div className="px-4 py-6 sm:px-6 border-b border-gray-200">
                  <div className="flex items-start justify-between">
                    <h2 className="text-lg font-medium text-gray-900">Saved Architectures</h2>
                    <button
                      onClick={togglePanel}
                      className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
                    >
                      <X className="h-6 w-6" />
                    </button>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">
                    View and load your previously saved architecture designs
                  </p>
                </div>
                
                {/* Panel content */}
                <div className="flex-1 overflow-y-auto p-4">
                  <SavedArchitectures onSelectArchitecture={handleSelectArchitecture} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SavedArchitecturesButton;