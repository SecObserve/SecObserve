import {
    Datagrid,
    FilterForm,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import { feature_license_management } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";

interface ProductGroupEmbeddedListProps {
    license_policy: any;
}

const showProductGroup = (id: any) => {
    return "../../../../product_groups/" + id + "/show";
};

function listFilters() {
    return [<TextInput source="name" alwaysOn />];
}

const ProductGroupEmbeddedList = ({ license_policy }: ProductGroupEmbeddedListProps) => {
    let filter = {};
    if (license_policy) {
        filter = { ...filter, license_policy: Number(license_policy.id) };
    }
    const listContext = useListController({
        filter: filter,
        perPage: 25,
        resource: "product_groups",
        sort: { field: "name", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: false,
        storeKey: "productgroups.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }
    localStorage.removeItem("productgroupembeddedlist.license_policy");
    if (license_policy) localStorage.setItem("productgroupembeddedlist.license_policy", license_policy.id);

    return (
        <ResourceContextProvider value="products">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={showProductGroup}
                        bulkActionButtons={false}
                        resource="products"
                    >
                        <TextField source="name" />
                        <TextField source="products_count" label="Products" />
                        <ObservationsCountField label="Active observations" withLabel={false} />
                        {feature_license_management() && (
                            <LicensesCountField label="Licenses / Components" withLabel={false} />
                        )}
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ProductGroupEmbeddedList;
