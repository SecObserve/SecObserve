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

import { AuthorizationGroupNameURLField } from "../../commons/custom_fields/AuthorizationGroupNameURLField";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { is_superuser } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";
import LicensePolicyAuthorizationGroupMemberAdd from "./LicensePolicyAuthorizationGroupMemberAdd";
import LicensePolicyAuthorizationGroupMemberEdit from "./LicensePolicyAuthorizationGroupMemberEdit";
import LicensePolicyAuthorizationGroupMemberRemove from "./LicensePolicyAuthorizationGroupMemberRemove";

function listFilters() {
    return [
        <TextInput source="name" alwaysOn />,
        <NullableBooleanInput source="is_manager" label="Manager" alwaysOn />,
    ];
}

type LicensePolicyAuthorizationGroupMemberEmbeddedListProps = {
    license_policy: any;
};

const LicensePolicyAuthorizationGroupMemberEmbeddedList = ({
    license_policy,
}: LicensePolicyAuthorizationGroupMemberEmbeddedListProps) => {
    const listContext = useListController({
        filter: { license_policy: Number(license_policy.id) },
        perPage: 25,
        resource: "license_policy_authorization_group_members",
        sort: { field: "authorization_group_data.name", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: true,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="license_policy_authorization_group_members">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {(is_superuser() || license_policy.is_manager) && (
                        <LicensePolicyAuthorizationGroupMemberAdd id={license_policy.id} />
                    )}
                    {license_policy.has_authorization_groups && (
                        <Fragment>
                            <FilterForm filters={listFilters()} />
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={false}
                                bulkActionButtons={false}
                                resource="license_policy_authorization_group_members"
                            >
                                <AuthorizationGroupNameURLField
                                    source="authorization_group_data.name"
                                    label="Authorization Group"
                                />
                                <BooleanField source="is_manager" label="Manager" />
                                {(is_superuser() || license_policy.is_manager) && (
                                    <WithRecord
                                        render={(license_policy_authorization_group_member) => (
                                            <Stack direction="row" spacing={4}>
                                                <LicensePolicyAuthorizationGroupMemberEdit />
                                                <LicensePolicyAuthorizationGroupMemberRemove
                                                    license_policy_authorization_group_member={
                                                        license_policy_authorization_group_member
                                                    }
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

export default LicensePolicyAuthorizationGroupMemberEmbeddedList;
