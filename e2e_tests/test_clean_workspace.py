import pytest

from helpers import disable_and_delete_resource


pytestmark = pytest.mark.asyncio


@pytest.mark.rossclean
@pytest.mark.timeout(3000)
async def test_ross_clean_workspace(admin_token, verify) -> None:

    # workspace_service_paths = ["/workspaces/9c208e42-1c4e-4670-83f5-f897a0b4f170/workspace-services/b52ff52e-e4f2-4393-8505-f08fb87ef190"]
    # for workspace_service_path in workspace_service_paths:
    #     await disable_and_delete_resource(f'/api{workspace_service_path}', 'workspace_service', workspace_owner_token, None, verify)

    workspace_paths = ["/workspaces/52826975-e571-4dd2-825c-8353f071da79"]
    for workspace_path in workspace_paths:
        await disable_and_delete_resource(f'/api{workspace_path}', admin_token, verify)
