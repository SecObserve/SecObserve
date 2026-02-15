import { Fragment } from "react";
import { CreateButton, Datagrid, List, TextField, TextInput, TopToolbar } from "react-admin";

import product_groups from ".";
import { PERMISSION_PRODUCT_GROUP_CREATE } from "../../access_control/types";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import { feature_license_management } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { getSettingListSize } from "../../commons/user_settings/functions";

const listFilters = [<TextInput source="name" alwaysOn />];

const ListActions = () => {
    const user = localStorage.getItem("user");
    return (
        <TopToolbar>
            {user && JSON.parse(user).permissions.includes(PERMISSION_PRODUCT_GROUP_CREATE) && <CreateButton />}
        </TopToolbar>
    );
};

const ProductGroupList = () => {
    return (
        <Fragment>
            <ListHeader icon={product_groups.icon} title="Product Groups" />
            <List
                perPage={25}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "name", order: "ASC" }}
                actions={<ListActions />}
                disableSyncWithLocation={false}
                storeKey="product_groups.list"
            >
                <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={false}>
                    <TextField source="name" />
                    <TextField source="products_count" label="Products" sortable={false} />
                    <ObservationsCountField label="Active observations" withLabel={false} />
                    {feature_license_management() && (
                        <LicensesCountField label="Licenses / Components" withLabel={false} />
                    )}
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default ProductGroupList;
