<p align="center">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=azure,terraform,vscode,python,react,vite,github" />
  </a>
</p>

<h1 align="center">AI Architecture Diagram Generator with MCP Validation</h1>

> **Intelligent Azure architecture diagram generator using AI agents, MCP service validation, and comprehensive Azure component library.**

## 🏗️ Architecture

This solution provides an intelligent system for generating professional Azure architecture documents and diagrams with automatic validation and correction:

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

1. **Azure subscription** with appropriate permissions
2. **Azure Developer CLI (azd)** installed ([Install Guide](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd))
3. **Azure CLI** installed ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
4. **Docker Desktop** installed and running ([Download](https://www.docker.com/products/docker-desktop))
5. **Git** installed ([Download](https://git-scm.com/downloads))

### Supported Regions

This template requires Azure AI Foundry, which is available in these regions:
- australiaeast, brazilsouth, canadaeast, eastus, eastus2, francecentral
- germanywestcentral, japaneast, southcentralus, southeastasia, southindia
- swedencentral, switzerlandnorth, uksouth, westus, westus3

> **Note**: Updates on limits and quotas: [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quotas-limits)

### Deployment


### Using Codespaces:

1. **Click the "Open in GitHub Codespaces" badge** above or visit the repository
2. **Create a new Codespace** - The environment will automatically configure itself
3. **Deploy to Azure** with just two commands:
   ```bash
   azd auth login
   azd up
   ```

No need to install anything locally - everything runs in the cloud! Perfect for developers who want to try the template quickly or work from any device.

```
## Remember you should have logged in with Azure CLI or switched to your target subscription:
```bash
az login
az account set --subscription <your-subscription-id>
```

**Option 2: Interactive Deployment (Recommended)**
```bash
azd init --template passadis/ai-architect-webapp
azd up
```

**Option 3: Non-Interactive Deployment**
```bash
azd init --template passadis/ai-architect-webapp -e <environment-name> --up
```

The deployment will:
- Create an Azure AI Foundry service with GPT-4o model
- Deploy frontend, backend, and MCP service containers
- Set up Cosmos DB, Storage Account, and Key Vault
- Configure managed identity and RBAC permissions
- Provide the application URL when complete

### Azure AI Agent Service

This deployment uses the **Basic Agent Setup** which includes:
- Azure AI Foundry service with Managed Identity authentication
- AI project with GPT-4o model deployment  
- Microsoft-managed Key Vault
- All necessary RBAC permissions

Alternative manual setup: [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fazure-ai-foundry%2Ffoundry-samples%2Frefs%2Fheads%2Fmain%2Fsamples%2Fmicrosoft%2Finfrastructure-setup%2F40-basic-agent-setup%2Fbasic-setup.json)

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

## ✨ What Makes This Project Special

- **🧠 Intelligent Architecture**: Combines Azure AI automation with a clean, maintainable codebase
- **📘 Model Context Protocol (MCP)**: Acts as a single source of truth for validation and service integration
- **🔗 Seamless Azure Integration**: Works effortlessly with Cosmos DB, Azure Storage, and other native services
- **⚙️ Scalable & Secure Backend**: Designed for high performance and enterprise-grade security
- **🖥️ Intuitive Frontend**: Responsive UI for a smooth and user-friendly experience
- **🧪 Clean Separation of Concerns**: Modular design for easier testing, maintenance, and innovation
- **🚀 azd Template Support**: Fully compatible with Azure Developer CLI for streamlined deployment
- **🏢 Enterprise Ready**: Built for real-world cloud environments with rapid iteration in mind

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

The application uses the following environment variables (automatically configured during deployment):

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

### Cloud-Native Development (Recommended)

This project is designed as a **cloud-native Azure template**. For the best development experience:

**Option 1: GitHub Codespaces**
```bash
# One-click cloud development environment
# Click "Code" → "Create codespace on main" in GitHub
# All dependencies and Azure CLI pre-configured
azd auth login
azd up
```

**Option 2: Azure Deployment**
```bash
# Deploy your development environment to Azure
azd init --template passadis/ai-architect-webapp
azd up
# Develop against live Azure services
```

**Option 3: Frontend-Only Local Development**
```bash
# Work on UI changes locally, use deployed Azure backend
cd frontend/architect-ai
npm install
npm start
# Configure REACT_APP_API_URL to point to your deployed Azure backend
```

### Why No Local Full-Stack Setup?

This template integrates deeply with Azure services (AI Foundry, Cosmos DB, Managed Identity) that don't have local equivalents. The architecture is optimized for Azure Container Apps with Dapr service mesh.

For learning and experimentation, we recommend deploying to Azure's free tier or using GitHub Codespaces.

### Testing

Once deployed to Azure, you can test the services:

```bash
# Test backend API health
curl https://your-backend-url.azurecontainerapps.io/health

# Test MCP service
curl https://your-mcp-service-url.azurecontainerapps.io/health

# View application logs
azd monitor --live
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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Azure Diagrams Library**: For the comprehensive Azure component library
- **Model Context Protocol**: For the validation framework
- **Azure Developer CLI**: For the deployment infrastructure
- **Community Contributors**: For feedback and improvements

---

**Made with ❤️ by [Konstantinos Passadis](https://github.com/passadis)**