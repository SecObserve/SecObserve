import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useNotify, useRefresh, useUpdate } from "react-admin";

import EditButton from "../../commons/custom_fields/EditButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { WebhookFields } from "./functions";

const WebhookEdit = () => {
    const [open, setOpen] = useState(false);
    const [update] = useUpdate();
    const refresh = useRefresh();
    const notify = useNotify();

    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason === "backdropClick") return;
        setOpen(false);
    };

    const webhookUpdate = (data: any) => {
        const patch = {
            name: data.name,
            url: data.url,
            event_types: data.event_types,
            min_severity: data.min_severity ?? "",
            active: data.active,
        };

        update(
            "webhooks",
            { id: data.id, data: patch },
            {
                onSuccess: () => {
                    refresh();
                    notify("Webhook updated", { type: "success" });
                    setOpen(false);
                },
                onError: (error: any) => {
                    notify(error.message, { type: "warning" });
                },
            }
        );
    };

    return (
        <Fragment>
            <EditButton title="Edit" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Edit webhook</DialogTitle>
                <DialogContent>
                    <SimpleForm onSubmit={webhookUpdate} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                        <WebhookFields />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default WebhookEdit;
