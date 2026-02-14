import { Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    ChipField,
    DateField,
    Labeled,
    RecordContextProvider,
    ReferenceField,
    TextField,
    useRecordContext,
} from "react-admin";

import observations from ".";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { useStyles } from "../../commons/layout/themes";
import ObservationShowDescriptionRecommendation from "./ObservationShowDescriptionRecommendation";

type ObservationShowHeaderProps = {
    observation?: any;
};

const ObservationShowHeader = ({ observation }: ObservationShowHeaderProps) => {
    const { classes } = useStyles();

    let in_observation_log = false;
    const observation_record = useRecordContext();
    if (observation) {
        in_observation_log = true;
    } else {
        observation = observation_record;
    }

    return (
        <RecordContextProvider value={observation}>
            {observation && (
                <Paper sx={{ marginBottom: 2, padding: 2 }}>
                    <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                        {!in_observation_log && (
                            <Fragment>
                                <observations.icon />
                                &nbsp;&nbsp;Observation
                            </Fragment>
                        )}
                        {in_observation_log && <Fragment>Observation</Fragment>}
                    </Typography>
                    {in_observation_log && (
                        <Stack direction="row" spacing={4} sx={{ marginBottom: 1 }}>
                            <Labeled label="Product">
                                <ReferenceField
                                    source="product_data.id"
                                    reference="products"
                                    queryOptions={{ meta: { api_resource: "product_names" } }}
                                    link="show"
                                    sx={{ "& a": { textDecoration: "none" } }}
                                >
                                    <TextField source="name" />
                                </ReferenceField>
                            </Labeled>
                            {observation.branch && (
                                <Labeled label="Branch/ Version">
                                    <TextField source="branch_name" />
                                </Labeled>
                            )}
                        </Stack>
                    )}
                    <Stack direction="row" spacing={4} sx={{ marginBottom: 1 }}>
                        <Stack spacing={2}>
                            <Labeled>
                                <SeverityField label="Severity" source="current_severity" />
                            </Labeled>
                            {observation.assessment_severity != "" && (
                                <Labeled>
                                    <TextField source="assessment_severity" />
                                </Labeled>
                            )}
                            {observation.rule_rego_severity != "" && (
                                <Labeled>
                                    <TextField source="rule_rego_severity" label="Rego rule severity" />
                                </Labeled>
                            )}
                            {observation.rule_severity != "" && (
                                <Labeled>
                                    <TextField source="rule_severity" label="Fields rule severity" />
                                </Labeled>
                            )}
                            {observation.parser_severity != "" &&
                                (observation.rule_rego_severity != "" ||
                                    observation.rule_severity != "" ||
                                    observation.assessment_severity != "") && (
                                    <Labeled>
                                        <TextField source="parser_severity" />
                                    </Labeled>
                                )}
                        </Stack>
                        <Stack spacing={2}>
                            <Labeled>
                                <ChipField source="current_status" label="Status" />
                            </Labeled>
                            {observation.assessment_status != "" && (
                                <Labeled>
                                    <TextField source="assessment_status" />
                                </Labeled>
                            )}
                            {observation.rule_rego_status != "" && (
                                <Labeled>
                                    <TextField source="rule_rego_status" label="Rego rule status" />
                                </Labeled>
                            )}
                            {observation.rule_status != "" && (
                                <Labeled>
                                    <TextField source="rule_status" label="Fields rule status" />
                                </Labeled>
                            )}
                            {observation.vex_status != "" && (
                                <Labeled label="VEX status">
                                    <TextField source="vex_status" />
                                </Labeled>
                            )}
                            {observation.parser_status != "" &&
                                (observation.rule_rego_status != "" ||
                                    observation.rule_status != "" ||
                                    observation.assessment_status != "" ||
                                    observation.vex_status != "") && (
                                    <Labeled>
                                        <TextField source="parser_status" />
                                    </Labeled>
                                )}
                        </Stack>
                        <Stack spacing={2}>
                            {observation.current_priority && (
                                <Labeled>
                                    <ChipField
                                        source="current_priority"
                                        label="Priority"
                                        sx={{
                                            width: "fit-content",
                                        }}
                                    />
                                </Labeled>
                            )}
                            {observation.assessment_priority && (
                                <Labeled>
                                    <TextField source="assessment_priority" />
                                </Labeled>
                            )}
                            {observation.rule_rego_priority && (
                                <Labeled>
                                    <TextField source="rule_rego_priority" label="Rego rule priority" />
                                </Labeled>
                            )}
                            {observation.rule_priority && (
                                <Labeled>
                                    <TextField source="rule_priority" label="Fields rule priority" />
                                </Labeled>
                            )}
                        </Stack>
                        {observation.found != null && (
                            <Labeled>
                                <DateField source="found" />
                            </Labeled>
                        )}
                        {observation.risk_acceptance_expiry_date != null && (
                            <Labeled label="Risk acceptance expiry">
                                <DateField source="risk_acceptance_expiry_date" />
                            </Labeled>
                        )}
                        {!in_observation_log && (
                            <Labeled>
                                <TextField source="title" className={classes.fontBigBold} />
                            </Labeled>
                        )}
                        {in_observation_log && (
                            <Labeled label="Title">
                                <ReferenceField
                                    source="id"
                                    reference="observations"
                                    queryOptions={{ meta: { api_resource: "observation_titles" } }}
                                    link="show"
                                    sx={{ "& a": { textDecoration: "none" } }}
                                >
                                    <TextField source="title" />
                                </ReferenceField>
                            </Labeled>
                        )}
                    </Stack>
                    <ObservationShowDescriptionRecommendation />
                </Paper>
            )}
        </RecordContextProvider>
    );
};

export default ObservationShowHeader;
