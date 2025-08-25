<p align="center">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=azure,terraform,vscode,python,react,vite,github" />
  </a>
</p>

<h1 align="center">AI Architecture Diagram Generator with MCP Validation</h1>


> **Intelligent Azure architecture diagram generator using AI agents, MCP service validation, and comprehensive Azure component library.**



## 🏗️ Architecture

This solution provides an intelligent system for generating professional Azure architecture diagrams with automatic validation and correction:

<img width="920" height="646" alt="ArchitectAIMCP" src="https://github.com/user-attachments/assets/6174b03e-76b3-45ed-887c-0fef5ae10cdd" />


## ✨ Features

### 🤖 **AI-Powered Generation**
- **Multi-Agent Architecture**: Specialized agents for design, validation, and diagram generation
- **GPT-4o Integration**: Advanced natural language processing for architecture understanding
- **Intelligent Component Selection**: Automatic Azure service recommendations

### 🔧 **MCP Validation Engine**
- **Component Validation**: Validates all Azure components against the official diagrams library
- **Automatic Correction**: Fixes import paths and component names automatically
- **Smart Suggestions**: Provides intelligent alternatives for invalid components
- **Comprehensive Coverage**: Supports 247+ Azure services across all categories

### 📊 **Professional Diagrams**
- **High-Quality Rendering**: Vector-based diagrams with professional styling
- **Multiple Formats**: PNG, SVG, and PDF output support
- **Responsive Design**: Works on desktop and mobile devices
- **Export Options**: Download diagrams in various formats

### 🛡️ **Enterprise-Ready**
- **Managed Identity**: Secure authentication without credentials
- **Cosmos DB Storage**: Persistent architecture storage and versioning
- **Container Apps**: Scalable, serverless container platform
- **Dapr Service to Service**: Seamless Service to Service Communications
- **Monitoring**: Comprehensive logging and monitoring with Application Insights

## 🚀 Quick Start

### Prerequisites
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Developer CLI](https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- Azure subscription with appropriate permissions
- Azure AI Foundry Agents Project in the same Subscription

### Deployment

1. **Clone the repository**:
   ```bash
   azd init --template passadis/ai-architect-mcp
   ```
 You will get asked to select an Environment name, Subscription and Region

 Once the build starts you will get asked to provide:

 Azure OpenAI API Key from your Azure OpenAI Agent Service

 Azure OpenAI Project Endpoint, in the format https://your-foundry-service.cognitiveservices.azure.com/your-foundry-project

 The Model Deployment name, which should be gpt-4o in most cases

## Azure AI Agent Service offers 2 types of setup:

### Basic :
 [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fazure-ai-foundry%2Ffoundry-samples%2Frefs%2Fheads%2Fmain%2Fsamples%2Fmicrosoft%2Finfrastructure-setup%2F40-basic-agent-setup%2Fbasic-setup.json)

Deploy a basic agent setup that uses Managed Identity for authentication.
An account and project are created.
A GPT-4o model is deployed.
A Microsoft-managed Key Vault is used by default.

### Standard:
 [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fazure-ai-foundry%2Ffoundry-samples%2Frefs%2Fheads%2Fmain%2Fsamples%2Fmicrosoft%2Finfrastructure-setup%2F41-standard-agent-setup%2Fazuredeploy.json)

Deploy a standard agent setup that uses Managed Identity for authentication.
An account and project are created.
A GPT-4o model is deployed.
Azure resources for storing customer data - Azure Storage, Azure Cosmos DB, and Azure AI Search - are automatically created if existing resources are't provided.
These resources are connected to your project to store files, threads, and vector data.
A Microsoft-managed Key Vault is used by default.


### ✨  What Makes This Project Special

- **🧠 Intelligent Architecture**: Combines Azure AI automation with a clean, maintainable codebase

- **📘 Model Context Protocol (MCP)**: Acts as a single source of truth for validation and service integration

- **🔗 Seamless Azure Integration**: Works effortlessly with Cosmos DB, Azure Storage, and other native services

- **⚙️ Scalable & Secure Backend**: Designed for high performance and enterprise-grade security

- **🖥️ Intuitive Frontend**: Responsive UI for a smooth and user-friendly experience

- **🧪 Clean Separation of Concerns**: Modular design for easier testing, maintenance, and innovation

- **🚀 azd Template Support**: Fully compatible with Azure Developer CLI for streamlined deployment

- **🏢 Enterprise Ready**: Built for real-world cloud environments with rapid iteration in mind


## Other methods:

## Prerequisites

1. Azure subscription
2. Azure CLI installed
3. Azure Developer CLI (azd) installed
4. Docker Desktop installed and running
5. Git installed

## 🚀 Quick Deploy with Azure Developer CLI

Deploy this entire solution to Azure with just two commands:

```bash
azd auth login
azd up
```
## Remember you should have logged in with Azure CLI or switched to your target subscription:
```bash
az login
az account set --subscription <your-subscription-id>
```

That's it! The `azd up` command will:
- Initialize the project environment
- Provision all Azure infrastructure using Terraform
- Build and deploy the containerized applications
- Configure managed identity and RBAC permissions
- Set up monitoring and logging

3. **Access the application**:
   - The deployment will output the frontend URL
   - Open the URL in your browser to start creating diagrams

## 💡 Usage Examples - Prompts

### Simple Web Application
```
Create a web application with a database and storage
```
**Generated**: App Service + SQL Database + Blob Storage with proper connections

### Microservices Architecture  
```
Design a microservices platform with API gateway, container apps, and shared database
```
**Generated**: API Management + Container Apps + Cosmos DB + Service Bus

### Data Analytics Pipeline
```
Build a data lake solution with Azure Functions for processing and Power BI for visualization
```
**Generated**: Data Lake + Functions + Event Hub + Power BI with data flow connections

## 🏛️ Architecture Components

### **Frontend** (React + TypeScript)
- Modern React application with TypeScript
- Material-UI components for professional interface
- Real-time diagram preview and editing
- Responsive design for all devices

### **Backend API** (FastAPI + Python)
- FastAPI web framework for high-performance APIs
- Azure AI Projects integration for GPT-4o access
- Multi-agent orchestration system
- Comprehensive error handling and logging

### **MCP Service** (Python + MCP Protocol)
- Model Context Protocol implementation
- Azure components validation engine
- Automatic import correction and suggestions
- GraphViz integration for diagram rendering

### **Infrastructure** (Terraform)
- Azure Container Apps for scalable hosting
- Cosmos DB for persistent storage
- Azure AI Projects for AI capabilities
- Managed Identity for secure authentication

## 🔧 Configuration

### Environment Variables

The application uses the following environment variables:

```bash
# Azure AI Projects
PROJECT_ENDPOINT=https://your-ai-project.cognitiveservices.azure.com
AI_AGENT_NAME=architectai-agent
VALIDATION_AGENT_NAME=architectai-validation-agent
MCP_DIAGRAM_AGENT_NAME=architectai-mcp-diagram-agent

# Azure Cosmos DB
COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com
COSMOS_DATABASE_NAME=ai-architect-db
COSMOS_CONTAINER_NAME=architectures

# Application Settings
MODEL_NAME=gpt-4o
DIAGRAMS_OUTPUT_DIR=static/diagrams
USE_MCP=true
```

### Advanced Configuration

For advanced scenarios, you can customize:

- **Agent Instructions**: Modify agent prompts in `backend/app/services/`
- **Component Mappings**: Update `mcp-service/azure_nodes.json`
- **Diagram Styling**: Customize rendering in `mcp-service/mcp_diagrams_server.py`
- **Infrastructure**: Modify Terraform files in `infra/`

## 🧪 Development

### Local Development Setup

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend/architect-ai
   npm install
   npm start
   ```

3. **MCP Service Setup**:
   ```bash
   cd mcp-service
   pip install -r requirements.txt
   python mcp_http_wrapper.py
   ```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend/architect-ai
npm test

# MCP Service tests
cd mcp-service
python -m pytest
```

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure Managed Identity is properly configured
   - Verify Azure AI Projects access permissions

2. **Diagram Generation Failures**:
   - Check MCP service health endpoint
   - Verify component names in logs

3. **Performance Issues**:
   - Monitor Application Insights for bottlenecks
   - Check Container Apps scaling configuration

### Support

- **Issues**: [GitHub Issues](https://github.com/passadis/ai-architect-webapp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/passadis/ai-architect-webapp/discussions)
- **Documentation**: [Wiki](https://github.com/passadis/ai-architect-webapp/wiki)

##  Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- **Azure Diagrams Library**: For the comprehensive Azure component library
- **Model Context Protocol**: For the validation framework
- **Azure Developer CLI**: For the deployment infrastructure
- **Community Contributors**: For feedback and improvements

## 🔗 Related Projects

- [Azure A2A Translation](https://github.com/passadis/azure-a2a-translation) - Agent-to-Agent translation service
- [Azure Container Apps Sample](https://github.com/passadis/react-semantic-kernel)
- [MS Learn MCP](https://github.com/passadis/mslearn-mcp-chat)

---

**Made with ❤️ by [Konstantinos Passadis](https://github.com/passadis)**
