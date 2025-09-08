# Configure the Azure Provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    azurecaf = {
      source  = "aztfmod/azurecaf"
      version = "~>1.2"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~>2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.1"
    }
  }
  required_version = ">= 1.5"
}

# Variable declarations
variable "location" {
  description = "The Azure region where resources will be created"
  type        = string
}

variable "prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "azure-ai-architect"
}

variable "environment_name" {
  description = "The environment name"
  type        = string
}

variable "model_name" {
  description = "Azure OpenAI Model Deployment Name"
  type        = string
  default     = "gpt-4o"
}

# Configure the Azure Provider
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# Get current client configuration
data "azurerm_client_config" "current" {}

# Generate a random suffix for unique resource names
resource "random_string" "resource_token" {
  length  = 13
  upper   = false
  special = false
}

# Generate resource names using azurecaf
resource "azurecaf_name" "resource_group" {
  name          = var.environment_name
  resource_type = "azurerm_resource_group"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "container_registry" {
  name          = var.environment_name
  resource_type = "azurerm_container_registry"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "container_apps_environment" {
  name          = var.environment_name
  resource_type = "azurerm_container_app_environment"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "log_analytics_workspace" {
  name          = var.environment_name
  resource_type = "azurerm_log_analytics_workspace"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "cosmos_account" {
  name          = var.environment_name
  resource_type = "azurerm_cosmosdb_account"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "storage_account" {
  name          = var.environment_name
  resource_type = "azurerm_storage_account"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "key_vault" {
  name          = var.environment_name
  resource_type = "azurerm_key_vault"
  random_length = 0
  clean_input   = true
}

resource "azurecaf_name" "user_assigned_identity" {
  name          = var.environment_name
  resource_type = "azurerm_user_assigned_identity"
  random_length = 0
  clean_input   = true
}

# Assign Key Vault Secrets Officer RBAC role to the Terraform runner
# This is required for the runner to create the secrets.
resource "azurerm_role_assignment" "key_vault_secrets_officer" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id

  depends_on = [azurerm_key_vault.main]
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = azurecaf_name.resource_group.result
  location = var.location

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# User Assigned Managed Identity
resource "azurerm_user_assigned_identity" "main" {
  name                = azurecaf_name.user_assigned_identity.result
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# Log Analytics Workspace for Container Apps
resource "azurerm_log_analytics_workspace" "main" {
  name                = azurecaf_name.log_analytics_workspace.result
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                        = azurecaf_name.key_vault.result
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"
  enable_rbac_authorization   = true


  tags = {
    "azd-env-name" = var.environment_name
  }
}

# Assign Key Vault Secrets User RBAC role to the Managed Identity
# This replaces the old access_policy block
resource "azurerm_role_assignment" "key_vault_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Azure AI Foundry (AI Hub)
resource "azapi_resource" "ai_foundry" {
  type      = "Microsoft.CognitiveServices/accounts@2025-04-01-preview"
  name      = "aifoundry-${substr(random_string.resource_token.result, 0, 8)}"
  parent_id = azurerm_resource_group.main.id
  location  = azurerm_resource_group.main.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "UserAssigned"
      userAssignedIdentities = {
        "${azurerm_user_assigned_identity.main.id}" = {}
      }
    }
    properties = {
      disableLocalAuth = false
      allowProjectManagement = true
      customSubDomainName = "aifoundry-${substr(random_string.resource_token.result, 0, 8)}"
    }
  }

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# GPT-4o Model Deployment
resource "azapi_resource" "gpt4o_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-10-01"
  parent_id = azapi_resource.ai_foundry.id
  name      = "gpt-4o"

  body = {
    sku = {
      capacity = 30
      name     = "GlobalStandard"
    }
    properties = {
      model = {
        name    = "gpt-4o"
        format  = "OpenAI"
        version = "2024-11-20"
      }
    }
  }

  depends_on = [azapi_resource.ai_foundry]
}

# Azure AI Project (as sub-resource of AI Foundry)
resource "azapi_resource" "ai_project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview"
  parent_id = azapi_resource.ai_foundry.id
  name      = "aiproj-${substr(random_string.resource_token.result, 0, 8)}"
  location  = azurerm_resource_group.main.location

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      description  = "AI Architect MCP Project"
      displayName  = "AI Architect Project"
    }
  }

  tags = {
    "azd-env-name" = var.environment_name
  }

  depends_on = [
    azapi_resource.ai_foundry
  ]
}

# Grant Cognitive Services OpenAI User role to managed identity
resource "azurerm_role_assignment" "openai_user" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Grant AI Developer role for AI project access
resource "azurerm_role_assignment" "ai_developer" {
  scope                = azapi_resource.ai_project.id
  role_definition_name = "Azure AI Developer"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Get the current subscription ID for the next role assignment
data "azurerm_subscription" "current" {}

# Assign Azure AI User RBAC role to the Managed Identity at the subscription level
resource "azurerm_role_assignment" "azure_ai_user" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Azure AI User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = azurecaf_name.container_registry.result
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# Grant ACR Pull permissions to managed identity
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = azurecaf_name.container_apps_environment.result
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# Storage Account for diagrams
resource "azurerm_storage_account" "main" {
  name                            = azurecaf_name.storage_account.result
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = true

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "PUT", "POST", "DELETE"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# Storage Container for diagrams
resource "azurerm_storage_container" "diagrams" {
  name                  = "diagrams"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"
}

# Grant Storage Blob Data Contributor to managed identity
resource "azurerm_role_assignment" "storage_blob_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# CosmosDB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = azurecaf_name.cosmos_account.result
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 86400
    max_staleness_prefix    = 1000000
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  tags = {
    "azd-env-name" = var.environment_name
  }
}

# CosmosDB SQL Database
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "ai-architect-db"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = 400
}

# CosmosDB SQL Container
resource "azurerm_cosmosdb_sql_container" "architectures" {
  name                  = "architectures"
  resource_group_name   = azurerm_resource_group.main.name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths   = ["/userId"]
  partition_key_version = 1
  throughput            = 400
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "cosmos_key" {
  name         = "cosmos-key"
  value        = azurerm_cosmosdb_account.main.primary_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.key_vault_secrets_officer]

}

resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.key_vault_secrets_officer]
}

# MCP Service Container App
resource "azurerm_container_app" "mcp_service" {
  name                         = "mcp-service"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.main.id]
  }

  # Enable DAPR for service-to-service communication
  dapr {
    app_id   = "mcp-service"
    app_port = 8001
  }


  template {
    container {
      name   = "mcp-service"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "PYTHONPATH"
        value = "/app"
      }
    }
    min_replicas = 1
    max_replicas = 3
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = false
    target_port                = 8001
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.main.id
  }

  tags = {
    "azd-env-name"     = var.environment_name
    "azd-service-name" = "mcp-service"
  }

  depends_on = [azurerm_role_assignment.acr_pull]
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.main.id]
  }

  # Enable DAPR for service-to-service communication
  dapr {
    app_id   = "backend"
    app_port = 8000
  }

  template {
    container {
      name   = "backend"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "USE_MCP"
        value = "true"
      }
      env {
        name  = "MCP_HTTP_SERVICE_URL"
        value = "https://${azurerm_container_app.mcp_service.name}.internal.${azurerm_container_app_environment.main.default_domain}"
      }
      env {
        name  = "USE_AZURE_SERVICES"
        value = "true"
      }
      env {
        name  = "AZURE_USE_MANAGED_IDENTITY"
        value = "true"
      }
      env {
        name  = "AZURE_AI_USE_MANAGED_IDENTITY"
        value = "true"
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.main.client_id
      }
      env {
        name  = "AZURE_COSMOS_ENDPOINT"
        value = azurerm_cosmosdb_account.main.endpoint
      }
      env {
        name        = "AZURE_COSMOS_KEY"
        secret_name = "cosmos-key"
      }
      env {
        name  = "AZURE_COSMOS_DATABASE_NAME"
        value = azurerm_cosmosdb_sql_database.main.name
      }
      env {
        name  = "AZURE_COSMOS_CONTAINER_NAME"
        value = azurerm_cosmosdb_sql_container.architectures.name
      }
      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }
      env {
        name  = "AZURE_STORAGE_CONTAINER_NAME"
        value = azurerm_storage_container.diagrams.name
      }
      env {
        name  = "AZURE_STORAGE_ACCOUNT_URL"
        value = azurerm_storage_account.main.primary_blob_endpoint
      }
      # Azure AI Foundry Configuration
      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = "https://${azapi_resource.ai_foundry.body.properties.customSubDomainName}.openai.azure.com/"
      }
      env {
        name  = "AZURE_AI_PROJECT_NAME"
        value = azapi_resource.ai_project.name
      }
      env {
        name  = "AZURE_AI_HUB_NAME"
        value = azapi_resource.ai_foundry.name
      }
      env {
        name  = "AZURE_OPENAI_DEPLOYMENT_NAME"
        value = azapi_resource.gpt4o_deployment.name
      }
      env {
        name  = "PROJECT_ENDPOINT"
        value = "https://${azapi_resource.ai_foundry.body.properties.customSubDomainName}.services.ai.azure.com/api/projects/${azapi_resource.ai_project.name}"
      }
      env {
        name  = "AZURE_OPENAI_API_VERSION"
        value = "2024-12-01-preview"
      }
      env {
        name  = "MODEL_NAME"
        value = var.model_name
      }
      env {
        name  = "DEPLOYMENT_NAME"
        value = var.model_name
      }
      env {
        name  = "AGENT_NAME"
        value = "architectai-design-agent"
      }
      env {
        name  = "DIAGRAM_AGENT_NAME"
        value = "architectai-diagram-agent"
      }
      env {
        name  = "VALIDATION_AGENT_NAME"
        value = "architectai-validation-agent"
      }
      env {
        name  = "MCP_HTTP_TIMEOUT"
        value = "60"
      }
      env {
        name  = "MCP_SERVER_PATH"
        value = "mcp_diagrams_server.py"
      }
    }
    min_replicas = 1
    max_replicas = 10
  }

  secret {
    name  = "cosmos-key"
    value = azurerm_cosmosdb_account.main.primary_key
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.main.primary_connection_string
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = false
    target_port                = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.main.id
  }

  tags = {
    "azd-env-name"     = var.environment_name
    "azd-service-name" = "backend"
  }

  depends_on = [azurerm_role_assignment.acr_pull, azurerm_container_app.mcp_service]
}

# Enable CORS for backend container app
resource "azapi_resource_action" "backend_cors" {
  type        = "Microsoft.App/containerApps@2024-03-01"
  resource_id = azurerm_container_app.backend.id
  method      = "PATCH"

  body = {
    properties = {
      configuration = {
        ingress = {
          corsPolicy = {
            allowedOrigins   = ["*"]
            allowedMethods   = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            allowedHeaders   = ["*"]
            allowCredentials = false
          }
        }
      }
    }
  }
  depends_on = [azurerm_container_app.backend]
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = "frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.main.id]
  }

  # Enable DAPR for service-to-service communication
  dapr {
    app_id   = "frontend"
    app_port = 80
  }

  template {
    container {
      name   = "frontend"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "NODE_ENV"
        value = "production"
      }
    }
    min_replicas = 1
    max_replicas = 5
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.main.id
  }

  tags = {
    "azd-env-name"     = var.environment_name
    "azd-service-name" = "frontend"
  }
  depends_on = [azurerm_role_assignment.acr_pull, azurerm_container_app.backend]
}