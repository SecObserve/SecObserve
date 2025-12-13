import { Fragment } from "react";
import {
    BooleanField,
    Datagrid,
    FieldProps,
    FilterForm,
    Identifier,
    ListContextProvider,
    NullableBooleanInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithRecord,
    useListController,
    useRecordContext,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { is_superuser } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";
import LicenseGroupLicenseAdd from "./LicenseGroupLicenseAdd";
import LicenseGroupLicenseRemove from "./LicenseGroupLicenseRemove";

function listFilters() {
    return [
        <TextInput source="spdx_id" label="SPDX Id" alwaysOn />,
        <TextInput source="name" alwaysOn />,
        <NullableBooleanInput source="is_osi_approved" label="OSI approved" alwaysOn />,
        <NullableBooleanInput source="is_deprecated" label="Deprecated" alwaysOn />,
    ];
}

export const LicenseIDURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? <TextUrlField text={record.spdx_id} url={showLicense(record.id)} /> : null;
};

const showLicense = (id: Identifier) => {
    return "#/licenses/" + id + "/show";
};

type LicenseGroupLicenseEmbeddedListProps = {
    license_group: any;
};

const LicenseGroupLicenseEmbeddedList = ({ license_group }: LicenseGroupLicenseEmbeddedListProps) => {
    const listContext = useListController({
        filter: { license_groups: Number(license_group.id) },
        perPage: 25,
        resource: "licenses",
        sort: { field: "spdx_id", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: true,
        storeKey: "licenseGroupLicenses.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="licenses">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {(is_superuser() || license_group.is_manager) && <LicenseGroupLicenseAdd id={license_group.id} />}
                    {license_group.has_licenses && (
                        <Fragment>
                            <FilterForm filters={listFilters()} />
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={false}
                                bulkActionButtons={false}
                                resource="users"
                            >
                                <LicenseIDURLField source="spdx_id" label="SPDX Id" />
                                <TextField source="name" label="Name" />
                                <BooleanField source="is_osi_approved" label="OSI approved" />
                                <BooleanField source="is_deprecated" label="Deprecated" />
                                {(is_superuser() || license_group.is_manager) && (
                                    <WithRecord
                                        render={(license) => (
                                            <LicenseGroupLicenseRemove
                                                license_group={license_group}
                                                license={license}
                                            />
                                        )}
                                    />
                                )}
                            </Datagrid>
                            <CustomPagination />
                        </Fragment>
                    )}
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default LicenseGroupLicenseEmbeddedList;
