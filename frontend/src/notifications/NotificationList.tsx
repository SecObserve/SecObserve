import { Fragment } from "react";
import {
    AutocompleteInput,
    BooleanInput,
    ChipField,
    Datagrid,
    DateField,
    FunctionField,
    List,
    ReferenceInput,
    SelectColumnsButton,
    TextField,
    TextInput,
    TopToolbar,
    WithListContext,
} from "react-admin";

import notifications from ".";
import { CustomPagination } from "../commons/custom_fields/CustomPagination";
import { has_attribute } from "../commons/functions";
import ListHeader from "../commons/layout/ListHeader";
import { AutocompleteInputMedium } from "../commons/layout/themes";
import { getSettingListSize } from "../commons/user_settings/functions";
import NotificationBulkMarkAsViewedButton from "./NotificationBulkMarkAsViewedButton";
import { TYPE_CHOICES } from "./types";

const messageShortened = (message: string | null) => {
    if (message && message.length > 255) {
        return message.substring(0, 255) + "...";
    }
    return message;
};

const listFilters = [
    <AutocompleteInput source="type" choices={TYPE_CHOICES} alwaysOn />,
    <TextInput source="name" alwaysOn />,
    <TextInput source="message" alwaysOn />,
    <TextInput source="function" alwaysOn />,
    <ReferenceInput
        source="product"
        reference="products"
        sort={{ field: "name", order: "ASC" }}
        queryOptions={{ meta: { api_resource: "product_names" } }}
        alwaysOn
    >
        <AutocompleteInputMedium optionText="name" />
    </ReferenceInput>,
    <ReferenceInput source="user" reference="users" sort={{ field: "full_name", order: "ASC" }} alwaysOn>
        <AutocompleteInputMedium optionText="full_name" />
    </ReferenceInput>,
    <BooleanInput source="exclude_already_viewed" alwaysOn />,
];

const BulkActionButtons = () => <NotificationBulkMarkAsViewedButton />;

const ListActions = () => (
    <TopToolbar>
        <SelectColumnsButton />
    </TopToolbar>
);

const NotificationList = () => {
    return (
        <Fragment>
            <ListHeader icon={notifications.icon} title="Notifications" />
            <List
                perPage={25}
                pagination={<CustomPagination />}
                filters={listFilters}
                filterDefaultValues={{ exclude_already_viewed: true }}
                sort={{ field: "created", order: "DESC" }}
                disableSyncWithLocation={false}
                storeKey="notifications.list"
                actions={<ListActions />}
            >
                <WithListContext
                    render={({ data }) => (
                        <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={<BulkActionButtons />}>
                            <TextField source="type" />
                            <TextField source="name" />
                            <DateField source="created" showTime={true} />
                            {has_attribute("message", data) && (
                                <FunctionField
                                    label="Message"
                                    render={(record) => messageShortened(record.message)}
                                    sortable={false}
                                    sx={{ wordBreak: "break-word" }}
                                />
                            )}
                            {has_attribute("function", data) && <TextField source="function" />}
                            {has_attribute("product_name", data) && <TextField source="product_name" label="Product" />}
                            {has_attribute("observation_title", data) && (
                                <TextField source="observation_title" label="Observation" />
                            )}
                            {has_attribute("user_full_name", data) && (
                                <TextField source="user_full_name" label="User" />
                            )}
                            <ChipField source="new_viewed" label="Status" sortable={false} />
                        </Datagrid>
                    )}
                />
            </List>
        </Fragment>
    );
};

export default NotificationList;
