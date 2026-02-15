import {
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import { SecurityGateTextField } from "../../commons/custom_fields/SecurityGateTextField";
import { humanReadableDate } from "../../commons/functions";
import { feature_license_management } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";
import { Product } from "../types";

interface ProductEmbeddedListProps {
    product_group?: any;
    license_policy?: any;
}

const showProduct = (id: any, resource: any, record: any) => {
    const license_policy_id = localStorage.getItem("productembeddedlist.license_policy");
    if (license_policy_id && record.has_licenses) {
        return "../../../../products/" + id + "/show/licenses";
    }
    return "../../../../products/" + id + "/show";
};

function listFilters() {
    return [<TextInput source="name" alwaysOn />];
}

const ProductEmbeddedList = ({ product_group, license_policy }: ProductEmbeddedListProps) => {
    let filter = {};
    if (product_group) {
        filter = { product_group: Number(product_group.id) };
    }
    if (license_policy) {
        filter = { ...filter, license_policy: Number(license_policy.id) };
    }
    const listContext = useListController({
        filter: filter,
        perPage: 25,
        resource: "products",
        sort: { field: "name", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: false,
        storeKey: "products.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }
    localStorage.removeItem("productembeddedlist.product_group");
    localStorage.removeItem("productembeddedlist.license_policy");
    if (product_group) localStorage.setItem("productembeddedlist.product_group", product_group.id);
    if (license_policy) localStorage.setItem("productembeddedlist.license_policy", license_policy.id);

    return (
        <ResourceContextProvider value="products">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={showProduct}
                        bulkActionButtons={false}
                        resource="products"
                    >
                        <TextField source="name" />
                        <TextField
                            source="repository_default_branch_name"
                            label="Default branch / version"
                            sortable={false}
                        />
                        <SecurityGateTextField label="Security gate" />
                        <ObservationsCountField label="Active observations" withLabel={false} />
                        {feature_license_management() &&
                            ((product_group &&
                                product_group.forbidden_licenses_count +
                                    product_group.review_required_licenses_count +
                                    product_group.unknown_licenses_count +
                                    product_group.allowed_licenses_count +
                                    product_group.ignored_licenses_count >
                                    0) ||
                                license_policy) && (
                                <LicensesCountField label="Licenses / Components" withLabel={false} />
                            )}
                        <FunctionField<Product>
                            label="Last observation change"
                            sortBy="last_observation_change"
                            render={(record) => (record ? humanReadableDate(record.last_observation_change) : "")}
                        />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ProductEmbeddedList;
