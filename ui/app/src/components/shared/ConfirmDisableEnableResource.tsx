import { Dialog, DialogFooter, PrimaryButton, DefaultButton, DialogType, Spinner } from '@fluentui/react';
import React, { useContext, useState } from 'react';
import { Resource } from '../../models/resource';
import { HttpMethod, ResultType, useAuthApiCall } from '../../hooks/useAuthApiCall';
import { WorkspaceContext } from '../../contexts/WorkspaceContext';
import { NotificationsContext } from '../../contexts/NotificationsContext';
import { ResourceType } from '../../models/resourceType';

interface ConfirmDisableEnableResourceProps {
  resource: Resource,
  isEnabled: boolean,
  onDismiss: () => void
}

// show a 'are you sure' modal, and then send a patch if the user confirms
export const ConfirmDisableEnableResource: React.FunctionComponent<ConfirmDisableEnableResourceProps> = (props: ConfirmDisableEnableResourceProps) => {
  const apiCall = useAuthApiCall();
  const [isSending, setIsSending] = useState(false);
  const workspaceCtx = useContext(WorkspaceContext);
  const opsCtx = useContext(NotificationsContext);

  const disableProps = {
    type: DialogType.normal,
    title: 'Disable Resource?',
    closeButtonAriaLabel: 'Close',
    subText: `Are you sure you want to disable ${props.resource.properties.display_name}?`,
  };

  const enableProps = {
    type: DialogType.normal,
    title: 'Enable Resource?',
    closeButtonAriaLabel: 'Close',
    subText: `Are you sure you want to enable ${props.resource.properties.display_name}?`,
  };

  const dialogStyles = { main: { maxWidth: 450 } };
  const modalProps = {
    titleAriaId: 'labelId',
    subtitleAriaId: 'subTextId',
    isBlocking: true,
    styles: dialogStyles
  };

  const wsAuth = (props.resource.resourceType === ResourceType.WorkspaceService || props.resource.resourceType === ResourceType.UserResource);

  const toggleDisableCall = async () => {
    setIsSending(true);
    let body = { isEnabled: props.isEnabled }
    let op = await apiCall(props.resource.resourcePath, HttpMethod.Patch, wsAuth ? workspaceCtx.workspaceClientId : undefined, body, ResultType.JSON, undefined, undefined, props.resource._etag);
    opsCtx.addOperations([op.operation]);
    setIsSending(false);
    props.onDismiss();
  }

  return (
  <>
    <Dialog
      hidden={false}
      onDismiss={() => props.onDismiss()}
      dialogContentProps={props.isEnabled ? enableProps : disableProps}
      modalProps={modalProps}
    >
      {!isSending ?
        <DialogFooter>
          {props.isEnabled ?
            <PrimaryButton text="Enable" onClick={() => toggleDisableCall()} />
            :
            <PrimaryButton text="Disable" onClick={() => toggleDisableCall()} />
          }
          <DefaultButton text="Cancel" onClick={() => props.onDismiss()} />

        </DialogFooter>
        :
        <Spinner label="Sending request..." ariaLive="assertive" labelPosition="right" />
      }
    </Dialog>
  </>);
};
