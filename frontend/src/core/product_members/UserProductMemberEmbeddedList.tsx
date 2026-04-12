import {
    Datagrid,
    Identifier,
    ListContextProvider,
    RaRecord,
    ResourceContextProvider,
    SelectField,
    TextField,
    useListController,
} from "react-admin";

import { ROLE_CHOICES } from "../../access_control/types";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";

type UserProductMemberEmbeddedListProps = {
    user: any;
    is_product_group: boolean;
};

function productLabel(is_product_group: boolean): string {
    return is_product_group ? "Product Group" : "Product";
}

const showProduct = (id: Identifier, resource: string, record: RaRecord) => {
    if (record.product_data.is_product_group) {
        return "../../../../product_groups/" + record.product_data.id + "/show/members";
    }
    return "../../../../products/" + record.product_data.id + "/show/members";
};

const UserProductMemberEmbeddedList = ({ user, is_product_group }: UserProductMemberEmbeddedListProps) => {
    const listContext = useListController({
        filter: { user: Number(user.id), is_product_group: is_product_group },
        perPage: getSettingRowsPerPage(),
        resource: "product_members",
        sort: { field: "product_data.name", order: "ASC" },
        disableSyncWithLocation: true,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="product_members">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={showProduct}
                        resource="product_members"
                    >
                        <TextField source="product_data.name" label={productLabel(is_product_group)} />
                        <SelectField source="role" choices={ROLE_CHOICES} />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default UserProductMemberEmbeddedList;
