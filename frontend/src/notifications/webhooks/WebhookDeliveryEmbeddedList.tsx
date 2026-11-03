import ReplayIcon from "@mui/icons-material/Replay";
import { Button } from "@mui/material";
import { MouseEvent } from "react";
import {
    Datagrid,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    WithRecord,
    useListController,
    useNotify,
    useRefresh,
} from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { DateField } from "../../commons/custom_fields/DateField";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { Webhook, WebhookDelivery } from "../types";

const prettyPayload = (payload: string) => {
    try {
        return JSON.stringify(JSON.parse(payload), null, 2);
    } catch {
        return payload;
    }
};

const PayloadExpand = () => (
    <WithRecord
        render={(delivery: WebhookDelivery) => (
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                {prettyPayload(delivery.payload)}
            </pre>
        )}
    />
);

const Redeliver = ({ delivery }: { delivery: WebhookDelivery }) => {
    const refresh = useRefresh();
    const notify = useNotify();

    const handleClick = (event: MouseEvent<HTMLElement>) => {
        event.stopPropagation();
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + `/webhook_deliveries/${delivery.id}/redeliver/`, {
            method: "POST",
        })
            .then(() => {
                refresh();
                notify("Delivery enqueued", { type: "success" });
            })
            .catch((error) => {
                notify(error.message, { type: "warning" });
            });
    };

    return (
        <Button size="small" onClick={handleClick} startIcon={<ReplayIcon />}>
            Redeliver
        </Button>
    );
};

type WebhookDeliveryEmbeddedListProps = {
    webhook: Webhook;
    canRedeliver: boolean;
};

const WebhookDeliveryEmbeddedList = ({ webhook, canRedeliver }: WebhookDeliveryEmbeddedListProps) => {
    const listContext = useListController({
        filter: { webhook: Number(webhook.id) },
        perPage: getSettingRowsPerPage(),
        resource: "webhook_deliveries",
        sort: { field: "created", order: "DESC" },
        disableSyncWithLocation: true,
        storeKey: "webhook_deliveries.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="webhook_deliveries">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick="expand"
                        expand={<PayloadExpand />}
                    >
                        <DateField source="created" showTime />
                        <TextField source="event_type" label="Event type" />
                        <TextField source="status" />
                        <TextField source="attempts" />
                        <TextField source="response_status_code" label="HTTP code" />
                        <TextField source="error" />
                        <WithRecord
                            render={(delivery: WebhookDelivery) =>
                                canRedeliver && delivery.status !== "Pending" ? <Redeliver delivery={delivery} /> : null
                            }
                        />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default WebhookDeliveryEmbeddedList;
