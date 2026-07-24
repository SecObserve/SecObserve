import SendIcon from "@mui/icons-material/Send";
import { useState } from "react";
import { Button, useNotify } from "react-admin";
import { useWatch } from "react-hook-form";

import { httpClient } from "../ra-data-django-rest-framework";

type WebhookTestButtonProps = {
    webhookSource: string;
    webhookType: "msteams" | "slack";
};

const WebhookTestButton = ({ webhookSource, webhookType }: WebhookTestButtonProps) => {
    const webhookUrl = useWatch({ name: webhookSource });
    const notify = useNotify();
    const [loading, setLoading] = useState(false);

    const handleTest = async () => {
        setLoading(true);
        try {
            const body: Record<string, unknown> = {
                webhook_url: webhookUrl,
                webhook_type: webhookType,
            };
            await httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/notifications/test_webhook/", {
                method: "POST",
                body: JSON.stringify(body),
            });
            notify("Test notification sent successfully", { type: "success" });
        } catch (e: unknown) {
            const message = e instanceof Error ? e.message : "unknown error";
            notify("Failed to send test notification: " + message, { type: "error" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Button
            label="Test"
            onClick={handleTest}
            disabled={loading || !webhookUrl}
            startIcon={<SendIcon />}
            size="small"
            sx={{ minWidth: "80px", height: "40px", alignSelf: "center", marginBottom: "20px" }}
        />
    );
};

export default WebhookTestButton;
