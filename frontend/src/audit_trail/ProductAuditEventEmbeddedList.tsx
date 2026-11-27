import { JsonViewer, JsonViewerTheme } from "@textea/json-viewer";
import {
    ChipField,
    Datagrid,
    FilterForm,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithRecord,
    useListController,
} from "react-admin";

import { getResolvedSettingTheme, getSettingListSize, getSettingRowsPerPage } from "../access_control/users/functions";
import { CustomPagination } from "../commons/custom_fields/CustomPagination";
import { DateField } from "../commons/custom_fields/DateField";
import { DateRangeFilter } from "../commons/custom_fields/DateRangeFilter";
import { AutocompleteInputMedium, useStyles } from "../commons/layout/themes";
import { OBJECT_TYPE_CHOICES, ProductAuditEvent } from "./types";

export const ChangesExpand = () => {
    const { classes } = useStyles();
    return (
        <WithRecord
            render={(event: ProductAuditEvent) => (
                <JsonViewer
                    value={event.changes}
                    groupArraysAfterLength={10000}
                    displayDataTypes={false}
                    displaySize={false}
                    indentWidth={4}
                    collapseStringsAfterLength={false}
                    enableClipboard={false}
                    className={classes.displayFontSize}
                    theme={getResolvedSettingTheme() as JsonViewerTheme}
                    sx={{ padding: 1 }}
                />
            )}
        />
    );
};

export const hasChanges = (event: ProductAuditEvent) => !!event.changes && Object.keys(event.changes).length > 0;

const listFilters = [
    <DateRangeFilter key="date" fields={[{ source: "created", label: "Created" }]} alwaysOn />,
    <AutocompleteInputMedium source="object_type" label="Object type" choices={OBJECT_TYPE_CHOICES} alwaysOn />,
    <TextInput source="q" label="Name" alwaysOn />,
];

type ProductAuditEventEmbeddedListProps = {
    // product or product group
    product: any;
};

const ProductAuditEventEmbeddedList = ({ product }: ProductAuditEventEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: getSettingRowsPerPage(),
        resource: "product_audit_events",
        sort: { field: "created", order: "DESC" },
        disableSyncWithLocation: true,
        storeKey: "product_audit_events.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="product_audit_events">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters} />
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick="expand"
                        expand={<ChangesExpand />}
                        isRowExpandable={hasChanges}
                        expandSingle
                    >
                        <DateField source="created" showTime />
                        <ChipField source="object_type" label="Object type" />
                        <TextField source="object_name" label="Name" />
                        <TextField source="action" />
                        <TextField source="user_full_name" label="User" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ProductAuditEventEmbeddedList;
