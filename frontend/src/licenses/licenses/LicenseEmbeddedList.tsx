import {
    BooleanField,
    Datagrid,
    FilterForm,
    ListContextProvider,
    NullableBooleanInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { useScancodeCategoryChoices } from "./functions";

const showLicense = (id: any) => {
    return "../../../../licenses/" + id + "/show";
};

function listFilters(categoryChoices: { id: string; name: string }[]) {
    return [
        <TextInput source="spdx_id" label="SPDX Id" alwaysOn />,
        <TextInput source="name" alwaysOn />,
        <NullableBooleanInput source="is_osi_approved" label="OSI approved" alwaysOn />,
        <NullableBooleanInput source="is_deprecated" label="Deprecated" alwaysOn />,
        <AutocompleteInputMedium source="scancode_category" label="Category" choices={categoryChoices} alwaysOn />,
    ];
}

type LicenseEmbeddedListProps = {
    license_group: any;
};

const LicenseEmbeddedList = ({ license_group }: LicenseEmbeddedListProps) => {
    const filter = license_group ? { license_groups: Number(license_group.id) } : {};
    const storeKey = license_group ? false : "licenses.embedded";

    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: "licenses",
        sort: { field: "spdx_id", order: "ASC" },
        disableSyncWithLocation: false,
        storeKey: storeKey,
    });
    const categoryChoices = useScancodeCategoryChoices(license_group?.id);

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="licenses">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters(categoryChoices)} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={showLicense}
                        bulkActionButtons={false}
                        resource="licenses"
                    >
                        <TextField source="spdx_id" label="SPDX Id" />
                        <TextField source="name" label="Name" />
                        <BooleanField source="is_osi_approved" label="OSI approved" textAlign="center" />
                        <BooleanField source="is_deprecated" label="Deprecated" textAlign="center" />
                        <TextField source="scancode_category" label="Category" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default LicenseEmbeddedList;
