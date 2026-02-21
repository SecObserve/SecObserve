import { Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    DateField,
    DeleteWithConfirmButton,
    Labeled,
    PrevNextButtons,
    Show,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import concluded_licenses from ".";
import { PERMISSION_CONCLUDED_LICENSE_DELETE } from "../../access_control/types";
import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";

const ShowActions = () => {
    const concluded_license = useRecordContext();

    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "product_data.name", order: "ASC" }}
                    storeKey="concluded_licenses.embedded"
                />
                {concluded_license?.product_data?.permissions?.includes(PERMISSION_CONCLUDED_LICENSE_DELETE) && (
                    <DeleteWithConfirmButton />
                )}
            </Stack>
        </TopToolbar>
    );
};

const ConcludedLicenseComponent = () => {
    return (
        <WithRecord
            render={(concluded_license) => (
                <Stack spacing={2} sx={{ marginBottom: 1, width: "100%" }}>
                    <Paper sx={{ marginBottom: 1, padding: 2 }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                                <concluded_licenses.icon />
                                &nbsp;&nbsp;Concluded license
                            </Typography>
                            <Labeled>
                                <ProductReferenceField
                                    label="Product"
                                    link={(record: any, reference: any) => `/${reference}/${record.id}/show/licenses`}
                                />
                            </Labeled>
                            <Labeled>
                                <TextField source="component_name_version" label="Component" />
                            </Labeled>
                            {concluded_license.manual_concluded_spdx_license_id && (
                                <Labeled>
                                    <TextField source="manual_concluded_spdx_license_id" label="SPDX license" />
                                </Labeled>
                            )}
                            {concluded_license.manual_concluded_license_expression && (
                                <Labeled>
                                    <TextField
                                        source="manual_concluded_license_expression"
                                        label="License expression"
                                    />
                                </Labeled>
                            )}
                            {concluded_license.manual_concluded_non_spdx_license && (
                                <Labeled>
                                    <TextField source="manual_concluded_non_spdx_license" label="Non-SPDX license" />
                                </Labeled>
                            )}
                            <Labeled>
                                <TextField source="user_data.full_name" label="User" />
                            </Labeled>
                            <Labeled>
                                <DateField source="last_updated" showTime />
                            </Labeled>
                        </Stack>{" "}
                    </Paper>
                </Stack>
            )}
        />
    );
};

const ConcludedLicenseShow = () => {
    return (
        <Show actions={<ShowActions />} component={ConcludedLicenseComponent}>
            <Fragment />
        </Show>
    );
};

export default ConcludedLicenseShow;
