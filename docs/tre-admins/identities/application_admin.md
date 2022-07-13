# The Application Administrator Identity

## Purpose
This identity's credentials are stored in the core key vault and are used when you wish to update AAD Applications. For instance, when you add Guacamole as a Workspace Service, you would need to add the URI of the Guacamole Service as a Redirect URI to the Workspace App to complete the login flow.

## Application Roles
This application does not have any roles defined.

## Microsoft Graph Permissions
| Name | Type* | Admin consent required |  TRE usage |
| --- | -- | -----| --------- |
| Application.ReadWrite.OwnedBy | Application | Yes | This user has `Application.ReadWrite.OwnedBy` as a minimum permission for it to function. If the tenant is managed by a customer administrator, then this user must be added to the **Owners** of every workspace that is created. This will allow TRE to manage the AAD Application. This will be a manual process for the Tenant Admin. |
| Application.ReadWrite.All | Application | Yes | If the AAD Administrator has delegated AAD administrative operations to the TRE, then this user should be granted `Application.ReadWrite.All`. This will allow the user to create workspace applications and administer any applications in the tenant. There will be no need for the Tenant Admin to oversee the Tenant. |

'*' See the difference between [delegated and application permission](https://docs.microsoft.com/graph/auth/auth-concepts#delegated-and-application-permissions) types. See [Microsoft Graph permissions reference](https://docs.microsoft.com/graph/permissions-reference) for more details.

## Clients
This user is currently only used from the Porter bundles hosted on the Resource Processor Virtual Machine Scale Set.

## How to create
```bash
./scripts/aad/create_application_administrator.sh \
--name "${TRE_ID}" --admin-consent --application-permission "${APPLICATION_PERMISSION}"
```
| Argument | Description |
| -------- | ----------- |
| `--name` | This is used to put a friendly name to the Application that can be seen in the portal. It is typical to use the name of your TRE instance. |
| `--admin-consent` | If you have the appropriate permission to grant admin consent, then pass in this argument. If you do not, you will have to ask an AAD Admin to consent after you have created the identity. Consent is required for this permission.
| `--application-permission` | This should be either `Application.ReadWrite.All` or `Application.ReadWrite.OwnedBy` |

## Environment Variables
| Variable | Description | Location |
| -------- | ----------- | -------- |
|APPLICATION_ADMIN_CLIENT_ID|The Client Id|`./templates/core/.env`|
|APPLICATION_ADMIN_CLIENT_SECRET|The client secret|`./templates/core/.env`|
