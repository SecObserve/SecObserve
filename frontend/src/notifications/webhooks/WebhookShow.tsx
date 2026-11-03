import SendIcon from "@mui/icons-material/Send";
import { Box, Button, Paper, Stack, Typography } from "@mui/material";
import { Fragment, useState } from "react";
import {
    BooleanField,
    Confirm,
    FunctionField,
    Labeled,
    PrevNextButtons,
    Show,
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
    const refresh = useRefresh();

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
            <WebhookSecretDialog
                secret={secret}
                onClose={() => {
                    setSecret(null);
                    refresh();
                }}
            />
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

const WebhookComponent = () => (
    <WithRecord
        render={(webhook: Webhook) => (
            <Box sx={{ width: "100%" }}>
                <Paper sx={{ marginBottom: 2, padding: 2 }}>
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Webhook
                    </Typography>
                    <Stack spacing={1}>
                        <Stack direction="row" spacing={4} useFlexGap sx={{ flexWrap: "wrap" }}>
                            <Labeled label="Name">
                                <TextField source="name" />
                            </Labeled>
                            <Labeled label="Scope">
                                <FunctionField render={(w: Webhook) => w.product_data?.name ?? "Global"} />
                            </Labeled>
                            <Labeled label="URL">
                                <TextField source="url" />
                            </Labeled>
                        </Stack>
                        <Stack direction="row" spacing={4} useFlexGap sx={{ flexWrap: "wrap" }}>
                            <Labeled label="Event types">
                                <FunctionField render={(w: Webhook) => w.event_types.join(", ")} />
                            </Labeled>
                            <Labeled label="Minimum severity">
                                <FunctionField render={(w: Webhook) => w.min_severity || "All"} />
                            </Labeled>
                            <Labeled label="Active">
                                <BooleanField source="active" />
                            </Labeled>
                            <Labeled label="Consecutive failures">
                                <TextField source="consecutive_failures" />
                            </Labeled>
                            {webhook.consecutive_failures > 0 && webhook.next_attempt_at && (
                                <Labeled label="Paused until">
                                    <DateField source="next_attempt_at" showTime />
                                </Labeled>
                            )}
                            <Labeled label="Created">
                                <DateField source="created" showTime />
                            </Labeled>
                            <Labeled label="Changed by">
                                <TextField source="user_full_name" emptyText="-" />
                            </Labeled>
                        </Stack>
                    </Stack>
                </Paper>
                <Paper sx={{ marginBottom: 2, padding: 2 }}>
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Deliveries
                    </Typography>
                    <WebhookDeliveryEmbeddedList webhook={webhook} canRedeliver={canEditWebhook(webhook)} />
                </Paper>
            </Box>
        )}
    />
);

const WebhookShow = () => (
    <Show actions={<ShowActions />} component={WebhookComponent}>
        <Fragment />
    </Show>
);

export default WebhookShow;
