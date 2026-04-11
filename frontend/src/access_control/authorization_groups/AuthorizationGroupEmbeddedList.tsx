import {
    Datagrid,
    FilterForm,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import CreateButton from "../../commons/custom_fields/CreateButton";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { is_external } from "../../commons/functions";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";

const ShowAuthorizationGroups = (id: any) => {
    return "../../../../authorization_groups/" + id + "/show";
};

function listFilters() {
    return [<TextInput source="name" alwaysOn />, <TextInput source="oidc_group" label="OIDC group" alwaysOn />];
}

type AuthorizationGroupEmbeddedListProps = {
    user: any;
};

const AuthorizationGroupEmbeddedList = ({ user }: AuthorizationGroupEmbeddedListProps) => {
    const filter = user ? { user: Number(user.id) } : {};
    const storeKey = user ? false : "authorization_groups.embedded";

    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: "authorization_groups",
        sort: { field: "name", order: "ASC" },
        filterDefaultValues: { is_active: true },
        disableSyncWithLocation: false,
        storeKey: storeKey,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="authorization_groups">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {!is_external() && !user && (
                        <CreateButton title="Add authorization group" to="/authorization_groups/create" />
                    )}
                    {!user && <FilterForm filters={listFilters()} />}
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={ShowAuthorizationGroups}
                        bulkActionButtons={false}
                        resource="authorization_groups"
                    >
                        <TextField source="name" />
                        <TextField source="oidc_group" label="OIDC group" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default AuthorizationGroupEmbeddedList;
