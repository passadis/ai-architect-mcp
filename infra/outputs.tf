# Output values for azd
output "AZURE_LOCATION" {
  value = azurerm_resource_group.main.location
}

output "AZURE_TENANT_ID" {
  value = data.azurerm_client_config.current.tenant_id
}

output "AZURE_RESOURCE_GROUP" {
  value = azurerm_resource_group.main.name
}

output "RESOURCE_GROUP_ID" {
  value = azurerm_resource_group.main.id
}

output "AZURE_CONTAINER_REGISTRY_ENDPOINT" {
  value = azurerm_container_registry.main.login_server
}

output "AZURE_CONTAINER_REGISTRY_NAME" {
  value = azurerm_container_registry.main.name
}

output "AZURE_CONTAINER_APPS_ENVIRONMENT_ID" {
  value = azurerm_container_app_environment.main.id
}

output "AZURE_CONTAINER_APPS_ENVIRONMENT_NAME" {
  value = azurerm_container_app_environment.main.name
}

output "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID" {
  value = azurerm_user_assigned_identity.main.client_id
}

output "AZURE_COSMOS_ENDPOINT" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "AZURE_COSMOS_DATABASE_NAME" {
  value = azurerm_cosmosdb_sql_database.main.name
}

output "AZURE_COSMOS_CONTAINER_NAME" {
  value = azurerm_cosmosdb_sql_container.architectures.name
}

output "AZURE_STORAGE_ACCOUNT_NAME" {
  value = azurerm_storage_account.main.name
}

output "AZURE_STORAGE_ACCOUNT_URL" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}

output "AZURE_STORAGE_CONTAINER_NAME" {
  value = azurerm_storage_container.diagrams.name
}

output "AZURE_KEY_VAULT_NAME" {
  value = azurerm_key_vault.main.name
}

output "AZURE_KEY_VAULT_URL" {
  value = azurerm_key_vault.main.vault_uri
}

output "FRONTEND_URL" {
  value = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "BACKEND_URL" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "MCP_SERVICE_URL" {
  value = "http://${azurerm_container_app.mcp_service.name}.internal.${azurerm_container_app_environment.main.default_domain}"
}

# Service endpoints for azd
output "FRONTEND_URI" {
  value = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "BACKEND_URI" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "MCP_SERVICE_URI" {
  value = "http://${azurerm_container_app.mcp_service.name}.internal.${azurerm_container_app_environment.main.default_domain}"
}

# Additional outputs needed for predeploy check
output "AZURE_COSMOS_CONNECTION_STRING_KEY" {
  value = azurerm_cosmosdb_account.main.name
}

output "AZURE_STORAGE_BLOB_URL" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}

output "AZURE_CLIENT_ID" {
  value = azurerm_user_assigned_identity.main.client_id
}

output "PROJECT_ENDPOINT" {
  value = "" # User will need to set this after creating Azure AI Projects resource
}

output "SERVICE_WEB_IDENTITY_PRINCIPAL_ID" {
  value = azurerm_user_assigned_identity.main.principal_id
}

output "WEB_URI" {
  value = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}
