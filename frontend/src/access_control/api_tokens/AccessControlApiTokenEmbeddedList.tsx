import {
    Datagrid,
    DateField,
    FilterForm,
    ListContextProvider,
    ReferenceField,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithRecord,
    useListController,
} from "react-admin";
import { Fragment } from "react/jsx-runtime";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ProductGroupReferenceField } from "../../commons/custom_fields/ProductGroupReferenceField";
import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";
import { getSettingListSize } from "../../commons/user_settings/functions";

function listFilters() {
    return [<TextInput source="name" id="api_token_name" alwaysOn />];
}

const AccessControlApiTokenEmbeddedList = () => {
    const listContext = useListController({
        filter: {},
        perPage: 25,
        resource: "api_tokens",
        sort: { field: "username", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: false,
        storeKey: "api_tokens.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="api_tokens">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={false}
                        bulkActionButtons={false}
                        resource="api_tokens"
                    >
                        <WithRecord
                            label="Username"
                            render={(api_token) => (
                                <Fragment>
                                    {(api_token.product || api_token.product_group) && <TextField source="username" />}
                                    {!api_token.product && !api_token.product_group && (
                                        <ReferenceField
                                            source="user"
                                            reference="users"
                                            link={(record: any, reference: any) =>
                                                `../../${reference}/${record.id}/show`
                                            }
                                            sx={{ "& a": { textDecoration: "none" } }}
                                        />
                                    )}
                                </Fragment>
                            )}
                        />
                        <WithRecord
                            label="Product"
                            render={(api_token) => (
                                <Fragment>
                                    {api_token.product && (
                                        <ProductReferenceField
                                            link={(record: any, reference: any) =>
                                                `../../${reference}/${record.id}/show/api_token`
                                            }
                                        />
                                    )}
                                </Fragment>
                            )}
                        />
                        <WithRecord
                            label="Product Group"
                            render={(api_token) => (
                                <Fragment>
                                    {api_token.product_group && (
                                        <ProductGroupReferenceField
                                            link={(record: any, reference: any) =>
                                                `../../${reference}/${record.id}/show/api_token`
                                            }
                                        />
                                    )}
                                </Fragment>
                            )}
                        />
                        <TextField source="name" />
                        <DateField source="expiration_date" />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default AccessControlApiTokenEmbeddedList;
