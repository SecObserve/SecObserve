import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { CreateBase, SimpleForm, useNotify, useRefresh } from "react-admin";

import AddButton from "../../commons/custom_fields/AddButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import WebhookSecretDialog from "./WebhookSecretDialog";
import { WebhookFields } from "./functions";

type WebhookCreateProps = {
    // null creates a global webhook
    product: any | null;
};

const WebhookCreate = ({ product }: WebhookCreateProps) => {
    const [open, setOpen] = useState(false);
    const [secret, setSecret] = useState<string | null>(null);
    const refresh = useRefresh();
    const notify = useNotify();

    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason === "backdropClick") return;
        setOpen(false);
    };

    const createWebhook = (data: any) => {
        const body = {
            product: product ? Number(product.id) : null,
            name: data.name,
            url: data.url,
            event_types: data.event_types,
            min_severity: data.min_severity ?? "",
            active: data.active,
        };

        // Not useCreate, so that the secret does not end up in the react-admin cache
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/webhooks/", {
            method: "POST",
            body: JSON.stringify(body),
        })
            .then((response) => {
                setSecret(response.json.secret);
                setOpen(false);
                refresh();
                notify("Webhook added", { type: "success" });
            })
            .catch((error) => {
                notify(error.message, { type: "warning" });
            });
    };

    return (
        <Fragment>
            <AddButton title="Add webhook" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Add webhook</DialogTitle>
                <DialogContent>
                    <CreateBase resource="webhooks">
                        <SimpleForm onSubmit={createWebhook} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                            <WebhookFields />
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
            <WebhookSecretDialog secret={secret} onClose={() => setSecret(null)} />
        </Fragment>
    );
};

export default WebhookCreate;
