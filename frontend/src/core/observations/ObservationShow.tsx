import { Box, Paper, Stack, TableHead, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    ArrayField,
    Datagrid,
    EditButton,
    Labeled,
    NumberField,
    PrevNextButtons,
    Show,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import {
    PERMISSION_OBSERVATION_ASSESSMENT,
    PERMISSION_OBSERVATION_EDIT,
    PERMISSION_OBSERVATION_LOG_APPROVAL,
} from "../../access_control/types";
import CVEFoundInField from "../../commons/custom_fields/CVEFoundInField";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import VulnerabilityIdField from "../../commons/custom_fields/VulnerabilityIdField";
import { get_cvss3_url, get_cvss4_url, get_cwe_url } from "../../commons/functions";
import AssessmentApproval from "../observation_logs/AssessmentApproval";
import ObservationLogEmbeddedList from "../observation_logs/ObservationLogEmbeddedList";
import { OBSERVATION_STATUS_ACTIVE, OBSERVATION_STATUS_IN_REVIEW } from "../types";
import ObservationAssessment from "./ObservationAssessment";
import ObservationRemoveAssessment from "./ObservationRemoveAssessment";
import ObservationsShowAside from "./ObservationShowAside";
import ObservationShowHeader from "./ObservationShowHeader";
import ObservationShowOrigins from "./ObservationShowOrigins";
import PotentialDuplicatesList from "./PotentialDuplicatesList";
import {
    IDENTIFIER_OBSERVATION_COMPONENT_LIST,
    IDENTIFIER_OBSERVATION_DASHBOARD_LIST,
    IDENTIFIER_OBSERVATION_EMBEDDED_LIST,
    IDENTIFIER_OBSERVATION_LIST,
    IDENTIFIER_OBSERVATION_REVIEW_LIST,
    IDENTIFIER_OBSERVATION_REVIEW_LIST_PRODUCT,
} from "./functions";

const ShowActions = () => {
    const observation = useRecordContext();
    let filter = null;
    let storeKey = null;
    let filterDefaultValues = {};

    if (localStorage.getItem(IDENTIFIER_OBSERVATION_LIST) === "true") {
        filter = {};
        filterDefaultValues = { current_status: OBSERVATION_STATUS_ACTIVE };
        storeKey = "observations.list";
    } else if (observation && localStorage.getItem(IDENTIFIER_OBSERVATION_EMBEDDED_LIST) === "true") {
        filter = { product: observation.product };
        storeKey = "observations.embedded";
    } else if (localStorage.getItem(IDENTIFIER_OBSERVATION_DASHBOARD_LIST) === "true") {
        filter = {
            age: "Past 7 days",
            current_status: OBSERVATION_STATUS_ACTIVE,
        };
        storeKey = "observations.dashboard";
    } else if (observation && localStorage.getItem(IDENTIFIER_OBSERVATION_REVIEW_LIST_PRODUCT) === "true") {
        filter = { product: observation.product, current_status: OBSERVATION_STATUS_IN_REVIEW };
        storeKey = "observations.review.product";
    } else if (localStorage.getItem(IDENTIFIER_OBSERVATION_REVIEW_LIST) === "true") {
        filter = { current_status: OBSERVATION_STATUS_IN_REVIEW };
        storeKey = "observations.review";
    } else if (observation && localStorage.getItem(IDENTIFIER_OBSERVATION_COMPONENT_LIST) === "true") {
        filter = {
            product: observation.product,
            branch: observation.branch,
            origin_service: observation.origin_service,
            origin_component_name_version: observation.origin_component_name_version,
            origin_component_purl_type: observation.origin_component_purl_type,
            current_status: OBSERVATION_STATUS_ACTIVE,
        };
        storeKey = "observations.component";
    }

    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                {filter && storeKey && (
                    <PrevNextButtons
                        filter={filter}
                        filterDefaultValues={filterDefaultValues}
                        queryOptions={{ meta: { api_resource: "observation_titles" } }}
                        linkType="show"
                        sort={{ field: "current_severity", order: "ASC" }}
                        storeKey={storeKey}
                    />
                )}
                {observation?.product_data?.permissions?.includes(PERMISSION_OBSERVATION_ASSESSMENT) && (
                    <ObservationAssessment />
                )}
                {observation?.product_data?.permissions?.includes(PERMISSION_OBSERVATION_ASSESSMENT) &&
                    (observation?.assessment_severity || observation?.assessment_status) && (
                        <ObservationRemoveAssessment />
                    )}
                {observation?.parser_data?.type == "Manual" &&
                    observation?.product_data?.permissions?.includes(PERMISSION_OBSERVATION_EDIT) && <EditButton />}
                {observation?.assessment_needs_approval &&
                    observation?.product_data?.permissions?.includes(PERMISSION_OBSERVATION_LOG_APPROVAL) && (
                        <AssessmentApproval observation_log_id={observation.assessment_needs_approval} />
                    )}
            </Stack>
        </TopToolbar>
    );
};

const EmptyDatagridHeader = () => <TableHead />;

const ObservationShowComponent = () => {
    return (
        <WithRecord
            render={(observation) => (
                <Box width={"100%"}>
                    <ObservationShowHeader />

                    {(observation.vulnerability_id != "" ||
                        observation.cvss3_score != null ||
                        observation.cvss3_vector != "" ||
                        observation.cvss4_score != null ||
                        observation.cvss4_vector != "" ||
                        observation.cwe != null ||
                        observation.epss_score != null ||
                        observation.epss_percentile != null) && (
                        <Paper sx={{ marginBottom: 2, padding: 2 }}>
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Vulnerability
                            </Typography>
                            <Stack direction="row" spacing={4}>
                                {observation.vulnerability_id != "" && (
                                    <Stack spacing={2}>
                                        <Labeled label="Vulnerability Id">
                                            <WithRecord
                                                render={(observation) => (
                                                    <VulnerabilityIdField
                                                        vulnerability_id={observation.vulnerability_id}
                                                    />
                                                )}
                                            />
                                        </Labeled>
                                        {observation.vulnerability_id_aliases &&
                                            observation.vulnerability_id_aliases.length > 0 && (
                                                <Labeled label="Aliases">
                                                    <Box>
                                                        <ArrayField source="vulnerability_id_aliases">
                                                            <Datagrid
                                                                bulkActionButtons={false}
                                                                header={EmptyDatagridHeader}
                                                                rowClick={false}
                                                                sx={{
                                                                    "& .RaDatagrid-rowCell": {
                                                                        paddingLeft: 0,
                                                                        borderBottom: 0,
                                                                        paddingBottom: "1px",
                                                                        paddingTop: "1px",
                                                                    },
                                                                }}
                                                            >
                                                                <WithRecord
                                                                    render={(alias) => (
                                                                        <VulnerabilityIdField
                                                                            vulnerability_id={alias.alias}
                                                                        />
                                                                    )}
                                                                />
                                                            </Datagrid>
                                                        </ArrayField>
                                                    </Box>
                                                </Labeled>
                                            )}
                                    </Stack>
                                )}
                                {(observation.cvss3_score != null ||
                                    observation.cvss3_vector != "" ||
                                    observation.cvss4_score != null ||
                                    observation.cvss4_vector != "") && (
                                    <Stack spacing={2}>
                                        {(observation.cvss4_score != null || observation.cvss4_vector != "") && (
                                            <Stack direction="row" spacing={2}>
                                                {observation.cvss4_score != null && (
                                                    <Labeled label="CVSS 4 score">
                                                        <NumberField source="cvss4_score" />
                                                    </Labeled>
                                                )}
                                                {observation.cvss4_vector != "" && (
                                                    <Labeled label="CVSS 4 vector">
                                                        <TextUrlField
                                                            label="CVSS 4 vector"
                                                            text={observation.cvss4_vector}
                                                            url={get_cvss4_url(observation.cvss4_vector)}
                                                            new_tab={true}
                                                        />
                                                    </Labeled>
                                                )}
                                            </Stack>
                                        )}
                                        {(observation.cvss3_score != null || observation.cvss3_vector != "") && (
                                            <Stack direction="row" spacing={2}>
                                                {observation.cvss3_score != null && (
                                                    <Labeled label="CVSS 3 score">
                                                        <NumberField source="cvss3_score" />
                                                    </Labeled>
                                                )}
                                                {observation.cvss3_vector != "" && (
                                                    <Labeled label="CVSS 3 vector">
                                                        <TextUrlField
                                                            label="CVSS 3 vector"
                                                            text={observation.cvss3_vector}
                                                            url={get_cvss3_url(observation.cvss3_vector)}
                                                            new_tab={true}
                                                        />
                                                    </Labeled>
                                                )}
                                            </Stack>
                                        )}
                                        {observation.cve_found_in && observation.cve_found_in.length > 0 && (
                                            <Labeled label="Exploit information found in">
                                                <CVEFoundInField
                                                    cve_found_in={observation.cve_found_in}
                                                    vulnerability_id={observation.vulnerability_id}
                                                />
                                            </Labeled>
                                        )}
                                    </Stack>
                                )}
                                {observation.cwe != null && (
                                    <Labeled>
                                        <TextUrlField
                                            label="CWE"
                                            text={observation.cwe}
                                            url={get_cwe_url(observation.cwe)}
                                            new_tab={true}
                                        />
                                    </Labeled>
                                )}
                                {observation.epss_score != null && (
                                    <Labeled label="EPSS score (%)">
                                        <NumberField source="epss_score" />
                                    </Labeled>
                                )}
                                {observation.epss_percentile != null && (
                                    <Labeled label="EPSS percentile (%)">
                                        <NumberField source="epss_percentile" />
                                    </Labeled>
                                )}
                            </Stack>
                        </Paper>
                    )}

                    <ObservationShowOrigins showDependencies={true} elevated={true} />

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ paddingBottom: 1, marginBottom: 1 }}>
                            Log
                        </Typography>
                        <ObservationLogEmbeddedList observation={observation} />
                    </Paper>

                    {observation?.has_potential_duplicates && (
                        <Paper sx={{ marginBottom: 2, paddingTop: 2, paddingLeft: 2, paddingRight: 2 }}>
                            <Typography variant="h6" sx={{ paddingBottom: 1, marginBottom: 1 }}>
                                Potential Duplicates
                            </Typography>
                            <PotentialDuplicatesList observation={observation} />
                        </Paper>
                    )}
                </Box>
            )}
        />
    );
};

const ObservationShow = () => {
    return (
        <Show actions={<ShowActions />} component={ObservationShowComponent} aside={<ObservationsShowAside />}>
            <Fragment />
        </Show>
    );
};

export default ObservationShow;
