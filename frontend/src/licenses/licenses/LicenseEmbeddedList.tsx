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

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";

const showLicense = (id: any) => {
    return "../../../../licenses/" + id + "/show";
};

const listFilters = [
    <TextInput source="spdx_id" label="SPDX Id" alwaysOn />,
    <TextInput source="name" alwaysOn />,
    <NullableBooleanInput source="is_osi_approved" label="OSI approved" alwaysOn />,
    <NullableBooleanInput source="is_deprecated" label="Deprecated" alwaysOn />,
];

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

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="licenses">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={showLicense}
                        bulkActionButtons={false}
                        resource="licenses"
                    >
                        <TextField source="spdx_id" label="SPDX Id" />
                        <TextField source="name" label="Name" />
                        <BooleanField source="is_osi_approved" label="OSI approved" />
                        <BooleanField source="is_deprecated" label="Deprecated" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default LicenseEmbeddedList;
