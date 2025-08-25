import React from 'react';
import { ArrowRight, Cpu, FileText, LayoutTemplate } from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <img src="/mainlogo.png" alt="ArchitectAI Logo" className="h-14 w-auto" />
          </div>
            <div>
              <button 
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                onClick={() => window.location.href = '/dashboard'}
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="relative bg-white overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                  <span className="block xl:inline">Transform ideas into</span>{' '}
                  <span className="block text-blue-600 xl:inline">architecture designs</span>
                </h1>
                <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  Describe your architectural needs in plain language, and our AI agents will collaborate to generate comprehensive design documents and diagrams.
                </p>
                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <a
                      href="/dashboard"
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10"
                    >
                      Start Designing
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </a>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </div>
        <div className="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 bg-gray-100 flex items-center justify-center">
          <div className="h-full w-full bg-gray-300 flex items-center justify-center text-gray-500">
                <img 
                src="/theme.png" 
                alt="Architecture Diagram" 
                className="h-full w-full object-overflow-hidden rounded-lg shadow-lg" 
              />
            <span className="ml-2 text-xl"></span>
          </div>
        </div>
      </div>

      {/* Feature Section */}
      <div className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              AI-Powered Architecture Design
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
              Transform your ideas into comprehensive architecture designs with our intelligent agents.
            </p>
          </div>

          <div className="mt-10">
            <div className="space-y-10 md:space-y-0 md:grid md:grid-cols-3 md:gap-x-8 md:gap-y-10">
              <div className="flex flex-col items-center md:items-start">
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                  <Cpu className="h-6 w-6" />
                </div>
                <div className="mt-5 text-center md:text-left">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Intelligent Agents</h3>
                  <p className="mt-2 text-base text-gray-500">
                    Multiple AI agents collaborate to create accurate and comprehensive designs.
                  </p>
                </div>
              </div>

              <div className="flex flex-col items-center md:items-start">
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                  <FileText className="h-6 w-6" />
                </div>
                <div className="mt-5 text-center md:text-left">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Design Documents</h3>
                  <p className="mt-2 text-base text-gray-500">
                    Automatically generated design documents that follow best practices.
                  </p>
                </div>
              </div>

              <div className="flex flex-col items-center md:items-start">
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                  <LayoutTemplate className="h-6 w-6" />
                </div>
                <div className="mt-5 text-center md:text-left">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Architecture Diagrams</h3>
                  <p className="mt-2 text-base text-gray-500">
                    Visual diagrams that clearly illustrate your system architecture.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-base text-gray-400">
            &copy; 2025 ArchitectAI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;