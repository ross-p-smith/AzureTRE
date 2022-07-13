# Configuring Shared Services

## Deploy/configure Nexus manually

Setting `DEPLOY_NEXUS=true` in your `.env` and running `make all` will install and configure certs & Nexus automatically. You can also
do this by running `make nexus-install`.

If you're deploying a brand new environment and you didn't flag Nexus to be installed automatically, you should deploy the VM-based (V2) service manually (read section `A`). If you wish to migrate from an existing App Service Nexus service (V1) to the VM-based service, first manually deploy the new service (section `A`) then proceed to section `B`.

!!! info
    Guacamole user resources of version `0.3.6` or higher target Nexus V2 by default, but have the option to manually specify V1 as a `nexus_version` parameter if you have an instance of the Nexus V1 service that you wish to use. When you're readu to migrate to the new service, you can do so manually by following section `B`.

### A. Deploy & configure V2 Nexus service (hosted on VM)

!!! caution
    Before deploying the V2 Nexus service, you will need workspaces of version `0.3.2` or above due to a dependency on a DNS zone link for the workspace(s) to connect to the Nexus VM.

Before deploying the Nexus shared service, you need to make sure that it will have access to a certificate to configure serving secure proxies. By default, the Nexus service will serve proxies from `https://nexus-{TRE_ID}.{LOCATION}.cloudapp.azure.com/`, and thus it requires a certificate that validates ownership of this domain to use for SSL.

You can use the Certs Shared Service to set one up by following these steps:

1. Run the below commands in your terminal to build, publish and register the certs bundle:

  ```cmd
  make bundle-build DIR=./templates/shared_services/certs
  make bundle-publish DIR=./templates/shared_services/certs
  make bundle-register DIR=./templates/shared_services/certs BUNDLE_TYPE=shared_service
  ```

2. Navigate to the Swagger UI for your TRE API at `https://<azure_tre_fqdn>/api/docs`, and authenticate if you haven't already by clicking `Authorize`.

3. Click `Try it out` on the `POST` `/api/shared-services` operation, and paste the following to deploy the certs service:

  ```json
  {
    "templateName": "tre-shared-service-certs",
    "properties": {
      "display_name": "Nexus cert",
      "description": "Generate/renew ssl cert for Nexus shared service",
      "domain_prefix": "nexus",
      "cert_name": "nexus-ssl"
    }
  }
  ```

!!! caution
    If you have KeyVault Purge Protection enabled and are re-deploying your environment using the same `cert_name`, you may encounter this: `Status=409 Code=\"Conflict\" Message=\"Certificate nexus-ssl is currently in a deleted but recoverable state`. You need to either manually recover the certificate or purge it before redeploying.

Once deployed, the certs service will use Letsencrypt to generate a certificate for the specified domain prefix followed by `-{TRE_ID}.{LOCATION}.cloudapp.azure.com`, so in our case, having entered `nexus`, this will be `nexus-{TRE_ID}.{LOCATION}.cloudapp.azure.com`, which will be the public domain for our Nexus service.

You can verify whether this has been successful by navigating to your core keyvault (`kv-{TRE_ID}`) and looking for a certificate called `nexus-ssl` (or whatever you called it).

After verifying the certificate has been generated, you can deploy Nexus:

1. Run the below commands in your terminal to build, publish and register the Nexus shared service bundle:

  ```cmd
  make bundle-build DIR=./templates/shared_services/sonatype-nexus-vm
  make bundle-publish DIR=./templates/shared_services/sonatype-nexus-vm
  make bundle-register DIR=./templates/shared_services/sonatype-nexus-vm BUNDLE_TYPE=shared_service
  ```

1. Navigate to the Swagger UI for your TRE API at `https://<azure_tre_fqdn>/api/docs`, and authenticate if you haven't already by clicking `Authorize`.

1. Click `Try it out` on the `POST` `/api/shared-services` operation, and paste the following to deploy the Nexus shared service:

  ```json
  {
    "templateName": "tre-shared-service-sonatype-nexus",
    "properties": {
      "display_name": "Nexus",
      "description": "Proxy public repositories with Nexus",
      "ssl_cert_name": "nexus-ssl"
    }
  }
  ```

!!! tip
    If you called your cert something different in the certs shared service step, make sure that is reflected above.

This will deploy the infrastructure required for Nexus, then start the service and configure it with the repository configurations located in the `./templates/shared_services/sonatype-nexus-vm/scripts/nexus_repos_config` folder. It will also set up HTTPS using the certificate you generated in the previous section, so proxies can be served at `https://nexus-{TRE_ID}.{LOCATION}.cloudapp.azure.com`.

You can optionally go to the Nexus web interface by visiting `https://nexus-{TRE_ID}.{LOCATION}.cloudapp.azure.com/` in the jumpbox and signing in with the username `admin` and the password secret located in your core keyvault, with the key `nexus-admin-password`. Here you should be able to see all of the configured repositories and you can use the UI to manage settings etc.

Just bear in mind that if this service is redeployed any changes made in the Nexus UI won't be persisted. If you wish to permanently add new repositories or alter existing ones, modify the JSON files within the `./nexus_repos_config` directory and redeploy.

### B. Migrate from an existing V1 Nexus service (hosted on App Service)

Once you've created the new V2 (VM-based) Nexus service by following section `A`, you can migrate from the V1 Nexus service by following these steps:

1. Identify any existing Guacamole user resources that are using the old proxy URL (`https://nexus-{TRE_ID}.azurewebsites.net/`). These will be any VMs with bundle versions < `0.3.2`.

1. These will need to be either **re-deployed** with the new template versions `0.3.2` or later and specifying an additional template parameter `"nexus_version"` with the value of `"V2"`, or manually have their proxy URLs updated by remoting into the VMs and updating the various configuration files of required package managers with the new URL (`https://nexus-{TRE_ID}.{LOCATION}.cloudapp.azure.com/`).

   1. For example, pip will need the `index`, `index-url` and `trusted-host` values in the global `pip.conf` file to be modified to use the new URL.

2. Once you've confirmed there are no dependencies on the old Nexus shared service, you can delete it using the API.

### Upgrade notes

The new V2 Nexus shared service can be located in the `./templates/shared_services/sonatype-nexus-vm` directory, with the bundle name `tre-shared-service-sonatype-nexus`, which is now hosted using a VM to enable additional configuration required for proxying certain repositories.

This has been created as a separate service as the domain name exposed for proxies will be different to the one used by the original Nexus service and thus will break any user resources configured with the old proxy URL.

The original Nexus service that runs on App Service (located in `./templates/shared_services/sonatype-nexus`) has the bundle name `tre-shared-service-nexus` so can co-exist with the new VM-based shared service to enable smoother upgrading of existing resources.

## Renewing certificates for Nexus

The Nexus V2 service checks Keyvault regularly for the latest certificate matching the name you passed on deploy (`nexus-ssl` by default).

When approaching expiry, you can either provide an updated certificate if you brought your own, or if you used the certs shared service to generate one, just call the `renew` custom action on that service. This will generate a new certificate and persist it to the Keyvault.

## Configure Gitea repositories

Note : This is a Gitea *shared service* which will be accessible from all workspaces intended for mirroring external Git repositories. A Gitea *workspace service* can also be deployed per workspace to enable Gitea to be used within a specific workspace.

By default, this Gitea instance does not have any repositories configured. You can add repositories to Gitea either by using the command line or by using the Gitea web interface.


### Command Line
Make sure you run the following commands using git bash and set your current directory as C:/AzureTRE.

1. On the jumbox, run:
```./templates/workspace_services/gitea/gitea_migrate_repo.sh -t <tre_id> -g <URL_of_github_repo_to_migrate>```
1. If you have issues with token or token doesn't work, you can reset the token by setting it's value to null in Key Vault:
```az keyvault secret set --name gitea-<tre-id>-admin-token --vault-name kv-<tre-id> --value null```

### Gitea Web Interface

1. on the jumbox, open Edge and go to:
```https://gitea-<TRE_ID>.azurewebsites.net/```
1. Authenticate yourself using username ```giteaadmin``` and the secret ```<gitea-TRE_ID-administrator-password>``` stored in the keyvault,
1. Add the repository of your choice

### Verify can access the mirrored repository

From a virtual machine within a workspace:
- Command line: ```git clone https://gitea-<TRE_ID>.azurewebsites.net/giteaadmin/<NameOfrepository>```
- Gitea Web Interface: ```https://gitea-<TRE_ID>.azurewebsites.net/```
