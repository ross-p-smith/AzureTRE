resource "azurerm_storage_account" "aml" {
  name                     = local.storage_name
  location                 = data.azurerm_resource_group.ws.location
  resource_group_name      = data.azurerm_resource_group.ws.name
  account_tier             = "Standard"
  account_replication_type = "GRS"
}

data "azurerm_private_dns_zone" "blobcore" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = local.core_resource_group_name
}

resource "azurerm_private_endpoint" "stgblobpe" {
  name                = "pe-${local.storage_name}"
  location            = data.azurerm_resource_group.ws.location
  resource_group_name = data.azurerm_resource_group.ws.name
  subnet_id           = data.azurerm_subnet.services.id

  lifecycle { ignore_changes = [tags] }

  private_dns_zone_group {
    name                 = "private-dns-zone-group"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.blobcore.id]
  }

  private_service_connection {
    name                           = "pesc-${local.storage_name}"
    private_connection_resource_id = azurerm_storage_account.aml.id
    is_manual_connection           = false
    subresource_names              = ["Blob"]
  }
}
