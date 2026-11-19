import { Stack } from "@mui/material";
import {
    BooleanField,
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    SelectInput,
    TextField,
    WithRecord,
    useListController,
} from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { Webhook } from "../types";
import WebhookDelete from "./WebhookDelete";
import WebhookEdit from "./WebhookEdit";
import { WebhookEventTypesField, canDeleteWebhook, canEditWebhook } from "./functions";

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

type WebhookEmbeddedListProps = {
    // product or product group
    product: any;
};

const WebhookEmbeddedList = ({ product }: WebhookEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: getSettingRowsPerPage(),
        resource: "webhooks",
        sort: { field: "name", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: "webhooks.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    localStorage.setItem("webhookembeddedlist", "true");

    return (
        <ResourceContextProvider value="webhooks">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters} />
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                    >
                        <FunctionField<Webhook>
                            label="Name"
                            sortBy="name"
                            render={(webhook) => (
                                <TextUrlField text={webhook.name} url={`#/webhooks/${webhook.id}/show`} />
                            )}
                        />
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
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default WebhookEmbeddedList;
