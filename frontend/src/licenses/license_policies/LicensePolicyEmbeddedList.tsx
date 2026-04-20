import {
    BooleanField,
    Datagrid,
    FilterForm,
    ListContextProvider,
    NullableBooleanInput,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import CreateButton from "../../commons/custom_fields/CreateButton";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { is_external } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";

const showLicensePolicy = (id: any) => {
    return "../../../../license_policies/" + id + "/show";
};

const listFilters = [
    <TextInput source="name" alwaysOn />,
    <ReferenceInput
        source="parent"
        reference="license_policies"
        // filter={{ is_child: false, is_not_id: license_policy.id }}
        sort={{ field: "name", order: "ASC" }}
        alwaysOn
    >
        <AutocompleteInputMedium optionText="name" />
    </ReferenceInput>,
    <NullableBooleanInput source="is_public" label="Public" alwaysOn />,
];

type LicensePolicyEmbeddedListProps = {
    license: any;
    license_group: any;
};

const LicensePolicyEmbeddedList = ({ license, license_group }: LicensePolicyEmbeddedListProps) => {
    let filter = {};
    let storeKey: any = "license_policies.embedded";
    if (license) {
        filter = { license: Number(license.id) };
        storeKey = false;
    }
    if (license_group) {
        filter = { license_group: Number(license_group.id) };
        storeKey = false;
    }

    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: "license_policies",
        sort: { field: "name", order: "ASC" },
        disableSyncWithLocation: false,
        storeKey: storeKey,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    localStorage.setItem("licensepolicyembeddedlist", "true");
    localStorage.removeItem("licenseotherlist");

    return (
        <ResourceContextProvider value="license_policies">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {!is_external() && !license && !license_group && (
                        <CreateButton title="Create license policy" to="/license_policies/create" />
                    )}
                    <FilterForm filters={listFilters} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={showLicensePolicy}
                        bulkActionButtons={false}
                        resource="license_policies"
                    >
                        <TextField source="name" label="Name" />
                        <TextField source="parent_name" label="Parent" />
                        <BooleanField source="is_public" label="Public" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default LicensePolicyEmbeddedList;
