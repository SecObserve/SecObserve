import {
    Datagrid,
    DateField,
    ListContextProvider,
    ResourceContextProvider,
    SelectField,
    SortPayload,
    TextField,
    WithRecord,
    useListController,
} from "react-admin";
import { Fragment } from "react/jsx-runtime";

import { PERMISSION_PRODUCT_API_TOKEN_REVOKE, ROLE_CHOICES } from "../../access_control/types";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import ApiTokenRevoke from "./ApiTokenRevoke";

type ApiTokenEmbeddedListProps = {
    type: "user" | "product";
    product?: any;
    user?: any;
};

const ApiTokenEmbeddedList = ({ type, product, user }: ApiTokenEmbeddedListProps) => {
    const filter = type === "product" ? { product: Number(product.id) } : { user: Number(user.id) };
    const sort: SortPayload = type === "product" ? { field: "role", order: "ASC" } : { field: "user", order: "ASC" };
    const resource = type === "product" ? "product_api_tokens" : "api_tokens";
    const current_user = localStorage.getItem("user");
    const username = current_user ? JSON.parse(current_user).username : "";

    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: resource,
        sort: sort,
        disableSyncWithLocation: true,
        storeKey: "api_tokens.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value={resource}>
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                    >
                        {type === "product" && <SelectField source="role" choices={ROLE_CHOICES} />}
                        <TextField source="name" />
                        <DateField source="expiration_date" />
                        <WithRecord
                            render={(api_token) => (
                                <Fragment>
                                    {((type === "product" &&
                                        product?.permissions.includes(PERMISSION_PRODUCT_API_TOKEN_REVOKE)) ||
                                        (type === "user" && api_token.username === username)) && (
                                        <ApiTokenRevoke
                                            type={type}
                                            api_token_id={api_token.id}
                                            user={user}
                                            name={api_token.name}
                                        />
                                    )}
                                </Fragment>
                            )}
                        />
                    </Datagrid>
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ApiTokenEmbeddedList;
