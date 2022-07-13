# TODO: Remove when have shared services support
# (tracked in https://github.com/microsoft/AzureTRE/issues/23)

data "azurerm_firewall" "fw" {
  name                = "fw-${var.tre_id}"
  resource_group_name = "rg-${var.tre_id}"


}

resource "null_resource" "az_login_sp" {

  count = var.arm_use_msi == true ? 0 : 1
  provisioner "local-exec" {
    command = "az login --service-principal --username ${var.arm_client_id} --password ${var.arm_client_secret} --tenant ${var.arm_tenant_id}"
  }

  triggers = {
    timestamp = timestamp()
  }

}

resource "null_resource" "az_login_msi" {

  count = var.arm_use_msi == true ? 1 : 0
  provisioner "local-exec" {
    command = "az login --identity -u '${data.azurerm_client_config.current.client_id}'"
  }

  triggers = {
    timestamp = timestamp()
  }
}

data "external" "rule_priorities" {
  program = ["bash", "-c", "./get_firewall_priorities.sh"]

  query = {
    firewall_name                = data.azurerm_firewall.fw.name
    resource_group_name          = data.azurerm_firewall.fw.resource_group_name
    service_resource_name_suffix = local.service_resource_name_suffix
  }
  depends_on = [
    null_resource.az_login_sp,
    null_resource.az_login_msi
  ]
}



resource "azurerm_firewall_network_rule_collection" "networkrulecollection" {
  name                = "nrc-${local.service_resource_name_suffix}"
  azure_firewall_name = data.azurerm_firewall.fw.name
  resource_group_name = data.azurerm_firewall.fw.resource_group_name
  priority            = data.external.rule_priorities.result.network_rule_priority
  action              = "Allow"

  rule {
    name = "allowStorage"

    source_addresses = data.azurerm_virtual_network.ws.address_space


    destination_ports = [
      "*"
    ]

    destination_addresses = local.allowed_service_tags

    protocols = [
      "TCP"
    ]
  }
}

resource "azurerm_firewall_application_rule_collection" "apprulecollection" {
  name                = "arc-${local.service_resource_name_suffix}"
  azure_firewall_name = data.azurerm_firewall.fw.name
  resource_group_name = data.azurerm_firewall.fw.resource_group_name
  priority            = data.external.rule_priorities.result.application_rule_priority
  action              = "Allow"

  rule {
    name = "allowMLrelated"

    source_addresses = data.azurerm_virtual_network.ws.address_space


    target_fqdns = local.allowed_urls

    protocol {
      port = "443"
      type = "Https"
    }
    protocol {
      port = "80"
      type = "Http"
    }
  }

  depends_on = [
    azurerm_firewall_network_rule_collection.networkrulecollection
  ]
}
