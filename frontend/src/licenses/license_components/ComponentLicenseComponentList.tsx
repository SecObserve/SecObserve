import {
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { EvaluationResultField } from "../../commons/custom_fields/EvaluationResultField";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { has_attribute } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { EVALUATION_RESULT_CHOICES } from "../types";
import { IDENTIFIER_LICENSE_COMPONENT_COMPONENT_LIST, setListIdentifier } from "./functions";

type ComponentLicenseComponentListProps = {
    component: any;
};

const licenseNameStyle = (type: string): string => {
    if (type === "" || type === "Non-SPDX" || type === "Multiple") {
        return "italic";
    }
    return "normal";
};

const ComponentLicenseComponentList = ({ component }: ComponentLicenseComponentListProps) => {
    setListIdentifier(IDENTIFIER_LICENSE_COMPONENT_COMPONENT_LIST);

    const showLicenseComponent = (id: any) => {
        return "../../../../license_components/" + id + "/show";
    };

    function listFilters() {
        const filters = [];
        filters.push(
            <AutocompleteInputMedium
                source="evaluation_result"
                label="Evaluation result"
                choices={EVALUATION_RESULT_CHOICES}
                alwaysOn
            />,
            <ProductReferenceInput alwaysOn />,
            <ProductGroupReferenceInput alwaysOn />,
            <TextInput source="branch_name" label="Branch / Version" alwaysOn />,
            <TextInput source="origin_service_name" label="Service" alwaysOn />
        );
        return filters;
    }

    const listContext = useListController({
        filter: { component: component.id },
        perPage: getSettingRowsPerPage(),
        resource: "license_components",
        sort: { field: "evaluation_result", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: "component_license_components.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="license_components">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={showLicenseComponent}
                                bulkActionButtons={false}
                                resource="license_components"
                            >
                                <FunctionField
                                    label="License"
                                    sortBy="effective_license_name"
                                    render={(record: any) => (
                                        <span style={{ fontStyle: licenseNameStyle(record.effective_license_type) }}>
                                            {record.effective_license_name}
                                        </span>
                                    )}
                                />
                                <EvaluationResultField
                                    source="evaluation_result"
                                    label="Evaluation result"
                                    sortable={true}
                                />
                                <TextField source="product_name" label="Product" />
                                {has_attribute("product_group_name", data, sort) && (
                                    <TextField source="product_group_name" label="Group" />
                                )}
                                {has_attribute("branch_name", data, sort) && (
                                    <TextField source="branch_name" label="Branch / Version" />
                                )}
                                {has_attribute("origin_service_name", data, sort) && (
                                    <TextField source="origin_service_name" label="Service" />
                                )}
                                {has_attribute("manual_concluded_comment", data, sort) && (
                                    <TextField source="manual_concluded_comment" />
                                )}
                            </Datagrid>
                        )}
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ComponentLicenseComponentList;
