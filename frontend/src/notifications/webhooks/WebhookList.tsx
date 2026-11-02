import { Stack } from "@mui/material";
import { Fragment } from "react";
import { BooleanField, Datagrid, List, SelectInput, TextField, TopToolbar, WithRecord } from "react-admin";

import webhooks from ".";
import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { is_superuser } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { Webhook } from "../types";
import WebhookCreate from "./WebhookCreate";
import WebhookDelete from "./WebhookDelete";
import WebhookEdit from "./WebhookEdit";
import { canDeleteWebhook, canEditWebhook } from "./functions";

const listFilters = [
    <SelectInput
        source="active"
        choices={[
            { id: "true", name: "Active" },
            { id: "false", name: "Inactive" },
        ]}
        alwaysOn
    />,
];

const ListActions = () => <TopToolbar>{is_superuser() && <WebhookCreate product={null} />}</TopToolbar>;

const WebhookList = () => (
    <Fragment>
        <ListHeader icon={webhooks.icon} title="Webhooks" />
        <List
            perPage={getSettingRowsPerPage()}
            pagination={<CustomPagination />}
            filters={listFilters}
            sort={{ field: "name", order: "ASC" }}
            actions={<ListActions />}
            disableSyncWithLocation={false}
            storeKey="webhooks.list"
        >
            <Datagrid size={getSettingListSize()} rowClick={false} bulkActionButtons={false}>
                <WithRecord
                    label="Name"
                    render={(webhook: Webhook) => (
                        <TextUrlField text={webhook.name} url={`#/webhooks/${webhook.id}/show`} />
                    )}
                />
                <WithRecord label="Scope" render={(webhook: Webhook) => webhook.product_data?.name ?? "Global"} />
                <TextField source="url" label="URL" />
                <WithRecord label="Event types" render={(webhook: Webhook) => webhook.event_types.join(", ")} />
                <BooleanField source="active" textAlign="center" />
                <TextField source="consecutive_failures" label="Consecutive failures" />
                <WithRecord
                    render={(webhook: Webhook) => (
                        <Stack direction="row" spacing={4}>
                            {canEditWebhook(webhook) && <WebhookEdit />}
                            {canDeleteWebhook(webhook) && <WebhookDelete webhook={webhook} />}
                        </Stack>
                    )}
                />
            </Datagrid>
        </List>
    </Fragment>
);

export default WebhookList;
