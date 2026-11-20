import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    Datagrid,
    FunctionField,
    List,
    SelectInput,
    TextField,
    TopToolbar,
    WithRecord,
} from "react-admin";

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
import { WebhookEventTypesField, WebhookScopeField, canDeleteWebhook, canEditWebhook } from "./functions";

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

const WebhookList = () => {
    localStorage.removeItem("webhookembeddedlist");

    return (
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
                empty={false}
            >
                <Datagrid size={getSettingListSize()} rowClick={false} bulkActionButtons={false}>
                    <FunctionField<Webhook>
                        label="Name"
                        sortBy="name"
                        render={(webhook) => <TextUrlField text={webhook.name} url={`#/webhooks/${webhook.id}/show`} />}
                    />
                    <WebhookScopeField label="Scope" sortBy="product_data.name" />
                    <TextField source="url" label="URL" />
                    <WebhookEventTypesField label="Event types" />
                    <BooleanField source="active" textAlign="center" />
                    <TextField source="consecutive_failures" label="Consecutive failures" />
                    <TextField source="user_full_name" label="Changed by" />
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
};

export default WebhookList;
