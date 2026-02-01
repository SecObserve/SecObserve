import { Box, Paper, TableHead, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    ArrayField,
    Datagrid,
    DateField,
    Labeled,
    ReferenceField,
    SimpleShowLayout,
    TextField,
    UrlField,
    WithRecord,
} from "react-admin";
import { Link } from "react-router-dom";

import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { is_superuser } from "../../commons/functions";
import { useLinkStyles } from "../../commons/layout/themes";
import { getResolvedSettingTheme } from "../../commons/user_settings/functions";

const ObservationsShowAside = () => {
    return (
        <Box width={"33%"} marginLeft={2} marginRight={1}>
            <MetaData />
            <References />
            <Evidences />
        </Box>
    );
};

const MetaData = () => {
    return (
        <Paper sx={{ marginBottom: 2 }}>
            <WithRecord
                render={(observation) => (
                    <SimpleShowLayout>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Metadata
                        </Typography>
                        <ReferenceField
                            source="product"
                            reference="products"
                            queryOptions={{ meta: { api_resource: "product_names" } }}
                            link="show"
                            sx={{ "& a": { textDecoration: "none" } }}
                        />
                        {observation.branch && <TextField label="Branch / Version" source="branch_name" />}
                        {observation.scanner != "" && <TextField source="scanner" />}
                        <TextField source="parser_data.name" label="Parser name" />
                        {observation.scanner_observation_id != "" && (
                            <TextField source="scanner_observation_id" label="Scanner observation id" />
                        )}
                        {observation.upload_filename != "" && <TextField source="upload_filename" />}
                        {observation.api_configuration_name != "" && (
                            <TextField source="api_configuration_name" label="API configuration" />
                        )}
                        {observation.general_rule != null && (
                            <ReferenceField
                                source="general_rule"
                                reference="general_rules"
                                label="General rule name"
                                link="show"
                                sx={{ "& a": { textDecoration: "none" } }}
                            />
                        )}
                        {observation.product_rule != null && (
                            <ReferenceField
                                source="product_rule"
                                reference="product_rules"
                                label="Product rule name"
                                link="show"
                                sx={{ "& a": { textDecoration: "none" } }}
                            />
                        )}
                        {is_superuser() && observation.vex_statement != null && (
                            <ReferenceField
                                source="vex_statement"
                                reference="vex/vex_statements"
                                label="VEX statement"
                                link="show"
                                sx={{ "& a": { textDecoration: "none" } }}
                            />
                        )}
                        {observation.issue_tracker_issue_id != "" && (
                            <Labeled>
                                <TextUrlField
                                    label="Issue"
                                    text={
                                        observation.product_data.issue_tracker_type +
                                        " #" +
                                        observation.issue_tracker_issue_id
                                    }
                                    url={observation.issue_tracker_issue_url}
                                    new_tab={true}
                                />
                            </Labeled>
                        )}
                        <DateField source="last_observation_log" label="Last change" showTime />
                        <DateField source="import_last_seen" label="Last seen" showTime />
                        <DateField source="created" showTime />
                    </SimpleShowLayout>
                )}
            />
        </Paper>
    );
};

const EmptyDatagridHeader = () => <TableHead />;

const References = () => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });

    return (
        <WithRecord
            render={(observation) => (
                <Fragment>
                    {observation.references && observation.references.length > 0 && (
                        <Paper sx={{ marginBottom: 2 }}>
                            <Typography variant="h6" sx={{ paddingLeft: 2, paddingTop: 1, marginBottom: 1 }}>
                                References
                            </Typography>
                            <ArrayField source="references" label={false}>
                                <Datagrid
                                    bulkActionButtons={false}
                                    header={EmptyDatagridHeader}
                                    sx={{ paddingBottom: 2 }}
                                    rowClick={false}
                                >
                                    <UrlField source="url" label={false} target="_blank" className={classes.link} />
                                </Datagrid>
                            </ArrayField>
                        </Paper>
                    )}
                </Fragment>
            )}
        />
    );
};

const Evidences = () => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });
    return (
        <WithRecord
            render={(observation) => (
                <Fragment>
                    {observation.evidences && observation.evidences.length > 0 && (
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
                                            <Link to={"/evidences/" + evidence.id + "/show"} className={classes.link}>
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

export default ObservationsShowAside;
