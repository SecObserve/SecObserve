import { useState } from "react";
import { Confirm, useDelete, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { Webhook } from "../types";

type WebhookDeleteProps = {
    webhook: Webhook;
    // called after a successful delete, e.g. to leave the show page
    onDeleted?: () => void;
};

const WebhookDelete = ({ webhook, onDeleted }: WebhookDeleteProps) => {
    const [open, setOpen] = useState(false);
    const [deleteOne] = useDelete();
    const refresh = useRefresh();
    const notify = useNotify();

    const handleConfirm = () => {
        deleteOne(
            "webhooks",
            { id: webhook.id },
            {
                onSuccess: () => {
                    notify("Webhook deleted");
                    refresh();
                    onDeleted?.();
                },
                onError: (error: any) => {
                    notify("Webhook could not be deleted: " + error.message, { type: "warning" });
                },
            }
        );
        setOpen(false);
    };

    return (
        <>
            <RemoveButton title="Delete" onClick={() => setOpen(true)} />
            <Confirm
                isOpen={open}
                title="Delete webhook"
                content={
                    "Are you sure you want to delete the webhook " + webhook.name + "? Its deliveries are deleted too."
                }
                onConfirm={handleConfirm}
                onClose={() => setOpen(false)}
            />
        </>
    );
};

export default WebhookDelete;
