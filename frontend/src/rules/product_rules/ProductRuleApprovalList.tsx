import {
    BooleanField,
    ChipField,
    Datagrid,
    FilterForm,
    ListContextProvider,
    ReferenceField,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { RULE_STATUS_NEEDS_APPROVAL } from "../types";

function listFilters() {
    return [
        <TextInput source="name" alwaysOn />,
        <ReferenceInput source="parser" reference="parsers" sort={{ field: "name", order: "ASC" }} alwaysOn>
            <AutocompleteInputMedium optionText="name" />
        </ReferenceInput>,
    ];
}

type ProductRuleApprovalListProps = {
    product: any;
};

const ProductRuleApprovalList = ({ product }: ProductRuleApprovalListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id), approval_status: RULE_STATUS_NEEDS_APPROVAL },
        perPage: getSettingRowsPerPage(),
        resource: "product_rules",
        sort: { field: "name", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: "product_rules.approval",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    const ShowProductRule = (id: any) => {
        return "../../../../product_rules/" + id + "/show";
    };

    localStorage.setItem("productruleapprovallist", "true");
    localStorage.removeItem("productruleembeddedlist");

    return (
        <ResourceContextProvider value="product_rules">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={ShowProductRule}
                        resource="product_rules"
                    >
                        <TextField source="name" sx={{ wordBreak: "break-word" }} />
                        <TextField source="new_severity" />
                        <TextField source="new_status" />
                        {product &&
                            (product.product_rules_need_approval ||
                                product.product_group_product_rules_need_approval) && (
                                <ChipField source="approval_status" />
                            )}
                        <BooleanField source="enabled" />
                        <ReferenceField
                            source="parser"
                            reference="parsers"
                            link={false}
                            sx={{ "& a": { textDecoration: "none" } }}
                        />
                        <TextField source="scanner_prefix" />
                        <TextField source="title" label="Observation title" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ProductRuleApprovalList;
