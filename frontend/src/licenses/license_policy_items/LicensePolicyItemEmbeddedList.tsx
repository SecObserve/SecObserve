import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    Datagrid,
    FieldProps,
    FilterForm,
    FunctionField,
    Identifier,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithRecord,
    useListController,
    useRecordContext,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { EvaluationResultField } from "../../commons/custom_fields/EvaluationResultField";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { is_superuser } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import { EVALUATION_RESULT_CHOICES } from "../types";
import LicensePolicyItemAdd from "./LicensePolicyItemAdd";
import LicensePolicyItemEdit from "./LicensePolicyItemEdit";
import LicensePolicyItemRemove from "./LicensePolicyItemRemove";

function listFilters() {
    return [
        <TextInput source="license_group_name" label="License group" alwaysOn />,
        <TextInput source="license_spdx_id" label="SPDX License" alwaysOn />,
        <TextInput source="license_expression" label="License expression" alwaysOn />,
        <TextInput source="non_spdx_license" label="Non-SPDX license" alwaysOn />,
        <AutocompleteInputMedium
            source="evaluation_result"
            label="Evaluation result"
            choices={EVALUATION_RESULT_CHOICES}
            alwaysOn
        />,
    ];
}

export const LicenseGroupNameURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? (
        <TextUrlField
            label="License group"
            text={record.license_group_name}
            url={showLicenseGroup(record.license_group)}
        />
    ) : null;
};

const showLicenseGroup = (id: Identifier) => {
    return "#/license_groups/" + id + "/show";
};

export const LicenseIDURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? <TextUrlField text={record.license_spdx_id} url={showLicense(record.license)} /> : null;
};

const showLicense = (id: Identifier) => {
    return "#/licenses/" + id + "/show";
};

export const commentShortened = (comment: string | null) => {
    if (comment && comment.length > 100) {
        return comment.substring(0, 96) + " ...";
    }
    return comment;
};

type LicensePolicyItemEmbeddedListProps = {
    license_policy: any;
};

const LicensePolicyItemEmbeddedList = ({ license_policy }: LicensePolicyItemEmbeddedListProps) => {
    const listContext = useListController({
        filter: { license_policy: Number(license_policy.id) },
        perPage: 25,
        resource: "license_policy_items",
        sort: { field: "evaluation_result", order: "ASC" },
        filterDefaultValues: {},
        disableSyncWithLocation: true,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="license_policy_items">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    {(is_superuser() || license_policy.is_manager) && <LicensePolicyItemAdd id={license_policy.id} />}
                    {license_policy.has_items && (
                        <Fragment>
                            <FilterForm filters={listFilters()} />
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={false}
                                bulkActionButtons={false}
                                resource="license_policy_item"
                            >
                                <LicenseGroupNameURLField source="license_group" label="License group" />
                                <LicenseIDURLField source="spdx_id" label="SPDX Id" />
                                <TextField source="license_expression" label="License expression" />
                                <TextField source="non_spdx_license" label="Non-SPDX license" />
                                <EvaluationResultField source="evaluation_result" label="Evaluation result" />
                                <FunctionField
                                    label="Comment"
                                    render={(record) => commentShortened(record.comment)}
                                    sortable={false}
                                    sx={{ wordBreak: "break-word" }}
                                />{" "}
                                {(is_superuser() || license_policy.is_manager) && (
                                    <WithRecord
                                        render={(license_policy_item) => (
                                            <Stack direction="row" spacing={4}>
                                                <LicensePolicyItemEdit
                                                    license_policy_id={license_policy.id}
                                                    license_policy_item_id={license_policy_item.id}
                                                />
                                                <LicensePolicyItemRemove license_policy_item={license_policy_item} />
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

export default LicensePolicyItemEmbeddedList;
