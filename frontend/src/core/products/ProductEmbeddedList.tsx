import {
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { DefaultBranchInput } from "../../commons/custom_fields/DefaultBranchInput";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { SecurityGateTextField } from "../../commons/custom_fields/SecurityGateTextField";
import { has_attribute, humanReadableDate } from "../../commons/functions";
import { feature_license_management } from "../../commons/functions";
import { Product } from "../types";

interface ProductEmbeddedListProps {
    product_group?: any;
    license_policy?: any;
    component?: any;
}

const showProduct = (id: any, resource: any, record: any) => {
    const license_policy_id = localStorage.getItem("productembeddedlist.license_policy");
    if (license_policy_id && record.has_licenses) {
        return "../../../../products/" + id + "/show/licenses";
    }
    return "../../../../products/" + id + "/show";
};

function listFilters(component: any) {
    const filters = [<TextInput source="name" alwaysOn />];
    if (component) {
        filters.push(
            <ProductGroupReferenceInput alwaysOn />,
            <DefaultBranchInput source="component_default_branch_only" label="Default branch only" alwaysOn />
        );
    }
    return filters;
}

const ProductEmbeddedList = ({ product_group, license_policy, component }: ProductEmbeddedListProps) => {
    let filter = {};
    if (product_group) {
        filter = { product_group: Number(product_group.id) };
    }
    if (license_policy) {
        filter = { ...filter, license_policy: Number(license_policy.id) };
    }
    if (component) {
        filter = { ...filter, component: Number(component.id) };
    }
    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: "products",
        sort: { field: "name", order: "ASC" },
        filterDefaultValues: {},
        // The tabs of a component share the URL, only the observations tab is synced with it
        disableSyncWithLocation: Boolean(component),
        storeKey: component ? "products.component" : "products.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }
    localStorage.removeItem("productembeddedlist.product_group");
    localStorage.removeItem("productembeddedlist.license_policy");
    localStorage.removeItem("productembeddedlist.component");
    if (product_group) localStorage.setItem("productembeddedlist.product_group", product_group.id);
    if (license_policy) localStorage.setItem("productembeddedlist.license_policy", license_policy.id);
    if (component) localStorage.setItem("productembeddedlist.component", component.id);

    return (
        <ResourceContextProvider value="products">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters(component)} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={showProduct}
                                bulkActionButtons={false}
                                resource="products"
                            >
                                <TextField source="name" />
                                {component && has_attribute("product_group_name", data, sort) && (
                                    <TextField source="product_group_name" label="Product Group" />
                                )}
                                {has_attribute("repository_default_branch_name", data, sort) && (
                                    <TextField
                                        source="repository_default_branch_name"
                                        label="Default branch / version"
                                        sortable={false}
                                    />
                                )}
                                {has_attribute("security_gate_passed", data, sort) && (
                                    <SecurityGateTextField label="Security gate" />
                                )}
                                {/* The counts are for the whole product and would be mistaken for the component's */}
                                {!component && <ObservationsCountField label="Active observations" withLabel={false} />}
                                {!component &&
                                    feature_license_management() &&
                                    has_attribute("all_licenses_count", data, sort) && (
                                        <LicensesCountField label="Licenses / Components" withLabel={false} />
                                    )}
                                <FunctionField<Product>
                                    label="Last observation change"
                                    sortBy="last_observation_change"
                                    render={(record) =>
                                        record ? humanReadableDate(record.last_observation_change) : ""
                                    }
                                />
                            </Datagrid>
                        )}
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ProductEmbeddedList;
