import { Box, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    ChipField,
    DateField,
    DeleteWithConfirmButton,
    Labeled,
    PrevNextButtons,
    ReferenceManyField,
    Show,
    SingleFieldList,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import csafs from ".";
import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";
import { delete_permission, update_permission } from "../functions";
import CSAFUpdate from "./CSAFUpdate";

const ShowActions = () => {
    const csaf = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "tracking_initial_release_date", order: "DESC" }}
                    storeKey="csaf.list"
                />
                {update_permission(csaf) && <CSAFUpdate />}
                {delete_permission(csaf) && <DeleteWithConfirmButton />}
            </Stack>
        </TopToolbar>
    );
};

const CSAFComponent = () => {
    return (
        <WithRecord
            render={(csaf) => (
                <Box width={"100%"}>
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                            <csafs.icon />
                            &nbsp;&nbsp;Exported CSAF document
                        </Typography>
                        <Stack spacing={1}>
                            {csaf?.product_data?.name && (
                                <Labeled>
                                    <ProductReferenceField label="Product" />
                                </Labeled>
                            )}
                            {csaf?.vulnerability_names && (
                                <Labeled>
                                    <ReferenceManyField
                                        reference="vex/csaf_vulnerabilities"
                                        target="csaf"
                                        label="Vulnerabilities"
                                    >
                                        <SingleFieldList linkType={false}>
                                            <ChipField source="name" />
                                        </SingleFieldList>
                                    </ReferenceManyField>
                                </Labeled>
                            )}
                            {csaf?.branch_names && (
                                <Labeled>
                                    <ReferenceManyField
                                        reference="vex/csaf_branches"
                                        target="csaf"
                                        label="Branches / Versions"
                                    >
                                        <SingleFieldList linkType={false}>
                                            <ChipField source="name" />
                                        </SingleFieldList>
                                    </ReferenceManyField>
                                </Labeled>
                            )}
                            <Labeled>
                                <TextField source="user_full_name" label="User" />
                            </Labeled>
                        </Stack>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Document
                            </Typography>{" "}
                            <Labeled>
                                <TextField source="document_id_prefix" label="ID prefix" />
                            </Labeled>
                            <Labeled>
                                <TextField source="document_base_id" label="Base ID" />
                            </Labeled>
                            <Labeled>
                                <TextField source="version" />
                            </Labeled>
                            <Labeled>
                                <TextField source="title" />
                            </Labeled>
                            <Labeled>
                                <TextField source="tlp_label" label="TLP label" />
                            </Labeled>
                        </Stack>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Tracking
                            </Typography>
                            <Labeled>
                                <DateField
                                    source="tracking_initial_release_date"
                                    showTime={true}
                                    label="Initial release date"
                                />
                            </Labeled>
                            <Labeled>
                                <DateField
                                    source="tracking_current_release_date"
                                    showTime={true}
                                    label="Current release date"
                                />
                            </Labeled>
                            <Labeled>
                                <TextField source="tracking_status" />
                            </Labeled>
                        </Stack>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Publisher
                            </Typography>
                            <Labeled>
                                <TextField source="publisher_name" />
                            </Labeled>
                            <Labeled>
                                <TextField source="publisher_category" />
                            </Labeled>
                            <Labeled>
                                <TextField source="publisher_namespace" />
                            </Labeled>
                        </Stack>
                    </Paper>
                </Box>
            )}
        />
    );
};

const CSAFShow = () => {
    return (
        <Show actions={<ShowActions />} component={CSAFComponent}>
            <Fragment />
        </Show>
    );
};

export default CSAFShow;
