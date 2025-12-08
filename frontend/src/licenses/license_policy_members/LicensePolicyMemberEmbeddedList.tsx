import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    Datagrid,
    FilterForm,
    ListContextProvider,
    NullableBooleanInput,
    ResourceContextProvider,
    TextInput,
    WithRecord,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { UserFullNameURLField } from "../../commons/custom_fields/UserFullNameURLField";
import { is_superuser } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";
import LicensePolicyMemberAdd from "./LicensePolicyMemberAdd";
import LicensePolicyMemberEdit from "./LicensePolicyMemberEdit";
import LicensePolicyMemberRemove from "./LicensePolicyMemberRemove";

function listFilters() {
    return [
        <TextInput source="full_name" alwaysOn />,
        <TextInput source="username" alwaysOn />,
        <NullableBooleanInput source="is_manager" label="Manager" alwaysOn />,
    ];
}

type LicensePolicyMemberEmbeddedListProps = {
    license_policy: any;
};

const LicensePolicyMemberEmbeddedList = ({ license_policy }: LicensePolicyMemberEmbeddedListProps) => {
    const listContext = useListController({
        filter: { license_policy: Number(license_policy.id) },
        perPage: 25,
        resource: "license_policy_members",
        sort: { field: "user_data.full_name", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: true,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="license_policy_members">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {(is_superuser() || license_policy.is_manager) && <LicensePolicyMemberAdd id={license_policy.id} />}
                    {license_policy.has_users && (
                        <Fragment>
                            <FilterForm filters={listFilters()} />
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={false}
                                bulkActionButtons={false}
                                resource="users"
                            >
                                <UserFullNameURLField source="user_data.full_name" label="User" />
                                <BooleanField source="is_manager" label="Manager" />
                                {(is_superuser() || license_policy.is_manager) && (
                                    <WithRecord
                                        render={(license_policy_member) => (
                                            <Stack direction="row" spacing={4}>
                                                <LicensePolicyMemberEdit />
                                                <LicensePolicyMemberRemove
                                                    license_policy_member={license_policy_member}
                                                />
                                            </Stack>
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

export default LicensePolicyMemberEmbeddedList;
