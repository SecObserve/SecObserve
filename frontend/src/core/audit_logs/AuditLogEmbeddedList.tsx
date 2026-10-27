import { Datagrid, ListContextProvider, ResourceContextProvider, TextField, useListController } from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { DateField } from "../../commons/custom_fields/DateField";

type AuditLogEmbeddedListProps = {
    product: any;
    is_product_group?: boolean;
};

const AuditLogEmbeddedList = ({ product, is_product_group = false }: AuditLogEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: getSettingRowsPerPage(),
        resource: "audit_logs",
        sort: { field: "created", order: "DESC" },
        disableSyncWithLocation: true,
        storeKey: "audit_logs.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="audit_logs">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                        resource="audit_logs"
                    >
                        <DateField source="created" showTime />
                        {/* A product shows the entries of its product group as well */}
                        {!is_product_group && <TextField source="product_name" label="Product" />}
                        <TextField source="user_name" label="User" emptyText="---" />
                        <TextField source="action" />
                        <TextField source="target" sx={{ wordBreak: "break-word" }} />
                        <TextField source="old_value" label="Old value" emptyText="---" sortable={false} />
                        <TextField source="new_value" label="New value" emptyText="---" sortable={false} />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default AuditLogEmbeddedList;
