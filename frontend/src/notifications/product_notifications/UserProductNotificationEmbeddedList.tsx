import {
    BooleanField,
    Datagrid,
    FunctionField,
    Identifier,
    ListContextProvider,
    RaRecord,
    ResourceContextProvider,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { NOTIFICATION_SETTINGS } from "../types";

type UserProductNotificationEmbeddedListProps = {
    user: any;
};

function productLabel(is_product_group: boolean): string {
    return is_product_group ? "Product Group" : "Product";
}

function productText(record: RaRecord): string {
    if (!record.product_data) {
        return "User template";
    }
    return record.product_data.name + " (" + productLabel(record.product_data.is_product_group) + ")";
}

const showProduct = (id: Identifier, resource: string, record: RaRecord) => {
    if (!record.product_data) {
        return false;
    }
    if (record.product_data.is_product_group) {
        return "../../../../product_groups/" + record.product_data.id + "/show/notifications";
    }
    return "../../../../products/" + record.product_data.id + "/show/notifications";
};

const UserProductNotificationEmbeddedList = ({ user }: UserProductNotificationEmbeddedListProps) => {
    const current_user = localStorage.getItem("user");
    const current_user_id = current_user ? JSON.parse(current_user).id : 0;
    // The notification settings of a product are always the ones of the logged in user,
    // so the rows make no sense as links while another user is shown
    const is_current_user = current_user_id == user.id;

    const listContext = useListController({
        filter: { user: Number(user.id) },
        perPage: getSettingRowsPerPage(),
        resource: "product_notifications",
        sort: { field: "product_data.name", order: "ASC" },
        disableSyncWithLocation: true,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="product_notifications">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={is_current_user ? showProduct : false}
                        resource="product_notifications"
                    >
                        <FunctionField
                            label="Product (Group)"
                            sortBy="product_data.name"
                            render={(record: RaRecord) => productText(record)}
                        />
                        {NOTIFICATION_SETTINGS.map((setting) => (
                            <BooleanField
                                key={setting.source}
                                source={setting.source}
                                label={setting.label}
                                textAlign="center"
                                sortable={false}
                            />
                        ))}
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default UserProductNotificationEmbeddedList;
