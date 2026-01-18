import {
    BooleanField,
    ChipField,
    Datagrid,
    FieldProps,
    FilterForm,
    ListContextProvider,
    ReferenceField,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithRecord,
    useListController,
    useRecordContext,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import RuleSimulation from "../RuleSimulation";
import { RULE_STATUS_CHOICES } from "../types";

function listFilters(product: any) {
    const filters = [
        <TextInput source="name" alwaysOn />,
        <ReferenceInput source="parser" reference="parsers" sort={{ field: "name", order: "ASC" }} alwaysOn>
            <AutocompleteInputMedium optionText="name" />
        </ReferenceInput>,
    ];
    if (product && (product.product_rules_need_approval || product.product_group_product_rules_need_approval)) {
        filters.push(
            <AutocompleteInputMedium
                source="approval_status"
                choices={RULE_STATUS_CHOICES}
                label="Approval status"
                alwaysOn
            />
        );
    }
    return filters;
}

const RuleNameURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? <TextUrlField text={record.name} url={get_rule_url(record.id)} /> : null;
};

function get_rule_url(rule_id: number): string {
    return `#/product_rules/${rule_id}/show`;
}

type ProductRuleEmbeddedListProps = {
    product: any;
};

const ProductRuleEmbeddedList = ({ product }: ProductRuleEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: 25,
        resource: "product_rules",
        sort: { field: "name", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: "product_rules.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    localStorage.setItem("productruleembeddedlist", "true");
    localStorage.removeItem("productruleapprovallist");

    return (
        <ResourceContextProvider value="product_rules">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters(product)} />
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                        resource="product_rules"
                    >
                        <RuleNameURLField source="name" />
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
                        <WithRecord render={(rule) => <RuleSimulation rule={rule} product={product} />} />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ProductRuleEmbeddedList;
