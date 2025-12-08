import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    Datagrid,
    FilterForm,
    Identifier,
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
import AuthorizationGroupMemberAdd from "./AuthorizationGroupMemberAdd";
import AuthorizationGroupMemberEdit from "./AuthorizationGroupMemberEdit";
import AuthorizationGroupMemberRemove from "./AuthorizationGroupMemberRemove";

function listFilters() {
    return [
        <TextInput source="full_name" alwaysOn />,
        <TextInput source="username" alwaysOn />,
        <NullableBooleanInput source="is_manager" label="Manager" alwaysOn />,
    ];
}

const showUser = (id: Identifier) => {
    return "#/users/" + id + "/show";
};

type AuthorizationGroupMemberEmbeddedListProps = {
    authorization_group: any;
};

const AuthorizationGroupMemberEmbeddedList = ({ authorization_group }: AuthorizationGroupMemberEmbeddedListProps) => {
    const listContext = useListController({
        filter: { authorization_group: Number(authorization_group.id) },
        perPage: 25,
        resource: "authorization_group_members",
        sort: { field: "user_data.full_name", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: false,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="authorization_group_members">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {(is_superuser() || authorization_group.is_manager) && (
                        <AuthorizationGroupMemberAdd id={authorization_group.id} />
                    )}
                    {authorization_group.has_users && (
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
                                {(is_superuser() || authorization_group.is_manager) && (
                                    <WithRecord
                                        render={(authorization_group_member) => (
                                            <Stack direction="row" spacing={4}>
                                                <AuthorizationGroupMemberEdit />
                                                <AuthorizationGroupMemberRemove
                                                    authorization_group_member={authorization_group_member}
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

export default AuthorizationGroupMemberEmbeddedList;
