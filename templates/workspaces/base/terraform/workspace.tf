resource "azurerm_resource_group" "ws" {
  location = var.location
  name     = "rg-${local.workspace_resource_name_suffix}"
  tags = merge(
    local.tre_workspace_tags,
    {
      project = "Azure Trusted Research Environment",
      source  = "https://github.com/microsoft/AzureTRE/"
    },
  )

  lifecycle { ignore_changes = [tags] }
}

// Networking is causing dependencies issues when some parts are deployed from
// Azure, especially for storage shares. It became quite difficult to figure out the needed
// dependencies for each resource seperatly, so to make it easier we packed all network
// resources as a single module that should be depended on.
module "network" {
  source                 = "./network"
  location               = var.location
  tre_id                 = var.tre_id
  address_space          = var.address_space
  ws_resource_group_name = azurerm_resource_group.ws.name
  tre_resource_id        = var.tre_resource_id
  tre_workspace_tags     = local.tre_workspace_tags
}

module "aad" {
  source                         = "./aad"
  tre_workspace_tags             = local.tre_workspace_tags
  count                          = var.register_aad_application ? 1 : 0
  key_vault_id                   = azurerm_key_vault.kv.id
  workspace_resource_name_suffix = local.workspace_resource_name_suffix
  workspace_owner_object_id      = var.workspace_owner_object_id
  aad_redirect_uris_b64          = var.aad_redirect_uris_b64
  depends_on = [
    azurerm_key_vault_access_policy.deployer,
    azurerm_key_vault_access_policy.resource_processor,
    null_resource.wait_for_dns_vault
  ]
}

module "airlock" {
  source                      = "./airlock"
  location                    = var.location
  tre_id                      = var.tre_id
  tre_workspace_tags          = local.tre_workspace_tags
  ws_resource_group_name      = azurerm_resource_group.ws.name
  enable_local_debugging      = var.enable_local_debugging
  services_subnet_id          = module.network.services_subnet_id
  short_workspace_id          = local.short_workspace_id
  airlock_processor_subnet_id = module.network.airlock_processor_subnet_id
  depends_on = [
    module.network,
  ]
}
