import { Box, Paper, Stack, TableHead, Typography } from "@mui/material";
import { Fragment } from "react";
import { ArrayField, Datagrid, DateField, Labeled, ReferenceField, TextField, WithRecord } from "react-admin";
import { Link } from "react-router-dom";

import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { useLinkStyles } from "../../commons/layout/themes";
import { getResolvedSettingTheme } from "../../commons/user_settings/functions";

const LicenseComponentShowAside = () => {
    return (
        <Box width={"33%"} marginLeft={2}>
            <MetaData />
            <Evidences />
        </Box>
    );
};

const MetaData = () => {
    return (
        <WithRecord
            render={(component) => (
                <Paper sx={{ marginBottom: 2, padding: 2 }}>
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Metadata
                    </Typography>
                    <Stack spacing={1}>
                        <Labeled label="Product">
                            <ReferenceField
                                source="product"
                                reference="products"
                                queryOptions={{ meta: { api_resource: "product_names" } }}
                                link={(record, reference) => `/${reference}/${record.id}/show/licenses`}
                                sx={{ "& a": { textDecoration: "none" } }}
                            />
                        </Labeled>
                        {component.license_policy_name != "" && (
                            <Labeled label="License policy">
                                <TextUrlField
                                    text={component.license_policy_name}
                                    url={"#/license_policies/" + component.license_policy_id + "/show"}
                                    label="License policy"
                                />
                            </Labeled>
                        )}
                        {component.branch_name && (
                            <Labeled label="Branch">
                                <TextField source="branch_name" />
                            </Labeled>
                        )}
                        {component.origin_service_name && (
                            <Labeled label="Service">
                                <TextField source="origin_service_name" />
                            </Labeled>
                        )}
                        {component.upload_filename != "" && (
                            <Labeled label="Upload filename">
                                <TextField source="upload_filename" />
                            </Labeled>
                        )}
                        <Labeled label="Last change">
                            <DateField source="last_change" showTime />
                        </Labeled>
                        <Labeled label="Last seen">
                            <DateField source="import_last_seen" showTime />
                        </Labeled>
                        <Labeled label="Created">
                            <DateField source="created" showTime />
                        </Labeled>
                    </Stack>
                </Paper>
            )}
        />
    );
};

const EmptyDatagridHeader = () => <TableHead />;

const Evidences = () => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });
    return (
        <WithRecord
            render={(license_component) => (
                <Fragment>
                    {license_component.evidences && license_component.evidences.length > 0 && (
                        <Paper sx={{ marginBottom: 2 }}>
                            <Typography variant="h6" sx={{ paddingLeft: 2, paddingTop: 1, marginBottom: 1 }}>
                                Evidences
                            </Typography>
                            <ArrayField source="evidences" label={false}>
                                <Datagrid
                                    bulkActionButtons={false}
                                    header={EmptyDatagridHeader}
                                    sx={{ paddingBottom: 2 }}
                                    rowClick={false}
                                >
                                    <WithRecord
                                        render={(evidence) => (
                                            <Link
                                                to={"/license_component_evidences/" + evidence.id + "/show"}
                                                className={classes.link}
                                            >
                                                {evidence.name}
                                            </Link>
                                        )}
                                    />
                                </Datagrid>
                            </ArrayField>
                        </Paper>
                    )}
                </Fragment>
            )}
        />
    );
};

export default LicenseComponentShowAside;
