import SendIcon from "@mui/icons-material/Send";
import { Button, Divider, Stack, Typography } from "@mui/material";
import { useState } from "react";
import {
    BooleanField,
    Confirm,
    PrevNextButtons,
    Show,
    SimpleShowLayout,
    TextField,
    TopToolbar,
    WithRecord,
    useNotify,
    useRecordContext,
    useRedirect,
    useRefresh,
} from "react-admin";

import { DateField } from "../../commons/custom_fields/DateField";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { Webhook } from "../types";
import WebhookDelete from "./WebhookDelete";
import WebhookDeliveryEmbeddedList from "./WebhookDeliveryEmbeddedList";
import WebhookEdit from "./WebhookEdit";
import WebhookSecretDialog from "./WebhookSecretDialog";
import { canDeleteWebhook, canEditWebhook } from "./functions";

const API = () => window.__RUNTIME_CONFIG__.API_BASE_URL + "/webhooks/";

const SendTest = ({ webhook }: { webhook: Webhook }) => {
    const notify = useNotify();
    const refresh = useRefresh();

    const handleClick = () => {
        httpClient(API() + `${webhook.id}/send_test/`, { method: "POST" })
            .then(({ json }) => {
                refresh();
                if (json.succeeded) {
                    notify(`Test delivered, HTTP ${json.status_code}`, { type: "success" });
                } else {
                    notify(`Test failed: ${json.error || "HTTP " + json.status_code}`, { type: "warning" });
                }
            })
            .catch((error) => notify(error.message, { type: "warning" }));
    };

    return (
        <Button size="small" onClick={handleClick} startIcon={<SendIcon />}>
            Send test
        </Button>
    );
};

const RotateSecret = ({ webhook }: { webhook: Webhook }) => {
    const [open, setOpen] = useState(false);
    const [secret, setSecret] = useState<string | null>(null);
    const notify = useNotify();

    const handleConfirm = () => {
        httpClient(API() + `${webhook.id}/rotate_secret/`, { method: "POST" })
            .then(({ json }) => {
                setOpen(false);
                setSecret(json.secret);
            })
            .catch((error) => {
                setOpen(false);
                notify(error.message, { type: "warning" });
            });
    };

    return (
        <>
            <Button size="small" onClick={() => setOpen(true)}>
                Rotate secret
            </Button>
            <Confirm
                isOpen={open}
                title="Rotate secret"
                content="The current secret stops working immediately. Receivers must be updated with the new secret."
                onConfirm={handleConfirm}
                onClose={() => setOpen(false)}
            />
            <WebhookSecretDialog secret={secret} onClose={() => setSecret(null)} />
        </>
    );
};

const ShowActions = () => {
    const webhook = useRecordContext<Webhook>();
    const redirect = useRedirect();
    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <PrevNextButtons linkType="show" sort={{ field: "name", order: "ASC" }} storeKey="webhooks.list" />
                {webhook && canEditWebhook(webhook) && <SendTest webhook={webhook} />}
                {webhook && canEditWebhook(webhook) && <RotateSecret webhook={webhook} />}
                {webhook && canEditWebhook(webhook) && <WebhookEdit />}
                {webhook && canDeleteWebhook(webhook) && (
                    <WebhookDelete webhook={webhook} onDeleted={() => redirect("list", "webhooks")} />
                )}
            </Stack>
        </TopToolbar>
    );
};

const WebhookShow = () => (
    <Show actions={<ShowActions />}>
        <WithRecord
            render={(webhook: Webhook) => (
                <>
                    <SimpleShowLayout>
                        <TextField source="name" />
                        <WithRecord label="Scope" render={(w: Webhook) => w.product_data?.name ?? "Global"} />
                        <TextField source="url" label="URL" />
                        <WithRecord label="Event types" render={(w: Webhook) => w.event_types.join(", ")} />
                        <WithRecord label="Minimum severity" render={(w: Webhook) => w.min_severity || "All"} />
                        <BooleanField source="active" />
                        <TextField source="consecutive_failures" label="Consecutive failures" />
                        {webhook.consecutive_failures > 0 && webhook.next_attempt_at && (
                            <DateField source="next_attempt_at" label="Paused until" showTime />
                        )}
                        <DateField source="created" showTime />
                    </SimpleShowLayout>
                    <Divider sx={{ marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Deliveries
                    </Typography>
                    <WebhookDeliveryEmbeddedList webhook={webhook} canRedeliver={canEditWebhook(webhook)} />
                </>
            )}
        />
    </Show>
);

export default WebhookShow;
