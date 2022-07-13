resource "azurerm_app_service" "nexus" {
  name                = "nexus-${var.tre_id}"
  resource_group_name = local.core_resource_group_name
  location            = data.azurerm_resource_group.rg.location
  app_service_plan_id = data.azurerm_service_plan.core.id
  https_only          = true
  tags                = local.tre_shared_service_tags

  app_settings = {
    APPINSIGHTS_INSTRUMENTATIONKEY      = data.azurerm_application_insights.core.instrumentation_key
    WEBSITES_PORT                       = "8081"          # nexus web-ui listens here
    WEBSITES_CONTAINER_START_TIME_LIMIT = "900"           # nexus takes a while to start-up
    WEBSITE_DNS_SERVER                  = "168.63.129.16" # required to access storage over private endpoints
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = false
    DOCKER_REGISTRY_SERVER_URL          = "https://index.docker.io/v1"
  }

  lifecycle { ignore_changes = [tags] }

  site_config {
    linux_fx_version            = "DOCKER|sonatype/nexus3"
    remote_debugging_enabled    = false
    scm_use_main_ip_restriction = true
    ftps_state                  = "Disabled"
    always_on                   = true
    min_tls_version             = "1.2"
    websockets_enabled          = false
    vnet_route_all_enabled      = true

    ip_restriction {
      action     = "Deny"
      ip_address = "0.0.0.0/0"
      name       = "Deny all"
      priority   = 2147483647
    }
  }

  storage_account {
    name         = "nexus-data"
    type         = "AzureFiles"
    account_name = data.azurerm_storage_account.nexus.name

    access_key = data.azurerm_storage_account.nexus.primary_access_key
    share_name = azurerm_storage_share.nexus.name
    mount_path = "/nexus-data"
  }

  logs {
    application_logs {
      file_system_level = "Information"
    }

    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 100
      }
    }
  }

  # App needs to wait for the properties file to be there
  depends_on = [
    null_resource.upload_nexus_props
  ]
}

resource "azurerm_private_endpoint" "nexus_private_endpoint" {
  name                = "pe-nexus-${var.tre_id}"
  resource_group_name = local.core_resource_group_name
  location            = data.azurerm_resource_group.rg.location
  subnet_id           = data.azurerm_subnet.shared.id
  tags                = local.tre_shared_service_tags

  private_service_connection {
    private_connection_resource_id = azurerm_app_service.nexus.id
    name                           = "psc-nexus-${var.tre_id}"
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "privatelink.azurewebsites.net"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.azurewebsites.id]
  }

  lifecycle { ignore_changes = [tags] }
}

resource "azurerm_app_service_virtual_network_swift_connection" "nexus-integrated-vnet" {
  app_service_id = azurerm_app_service.nexus.id
  subnet_id      = data.azurerm_subnet.web_app.id
}

resource "azurerm_monitor_diagnostic_setting" "nexus" {
  name                       = "diag-${var.tre_id}"
  target_resource_id         = azurerm_app_service.nexus.id
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.tre.id

  log {
    category = "AppServiceHTTPLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServiceConsoleLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServiceAppLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServiceFileAuditLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServiceAuditLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServiceIPSecAuditLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServicePlatformLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  log {
    category = "AppServiceAntivirusScanAuditLogs"
    enabled  = true

    retention_policy {
      days    = 1
      enabled = false
    }
  }

  metric {
    category = "AllMetrics"
    enabled  = true

    retention_policy {
      enabled = false
    }
  }
}

resource "azurerm_storage_share" "nexus" {
  name                 = "nexus-data"
  storage_account_name = data.azurerm_storage_account.nexus.name
  quota                = var.nexus_storage_limit
}

# Include a properties file in the nexus-data path will change its configuration. We need this to instruct it not to create default repositories.
resource "null_resource" "upload_nexus_props" {
  provisioner "local-exec" {
    command = <<EOT
      az storage directory create \
      --name etc --share-name  ${azurerm_storage_share.nexus.name} \
      --account-name ${data.azurerm_storage_account.nexus.name} \
      --account-key ${data.azurerm_storage_account.nexus.primary_access_key} && \
      az storage file upload --source ${var.nexus_properties_path} \
      --path etc --share-name  ${azurerm_storage_share.nexus.name} \
      --account-name ${data.azurerm_storage_account.nexus.name} \
      --account-key ${data.azurerm_storage_account.nexus.primary_access_key}
      EOT
  }

  # Make sure this only runs after the share is ready
  depends_on = [
    azurerm_storage_share.nexus
  ]
}
