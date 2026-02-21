import { Box, Paper, Stack, Typography } from "@mui/material";
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
import { Fragment } from "react/jsx-runtime";

import cyclonedxs from ".";
import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";
import { delete_permission, update_permission } from "../functions";
import CycloneDXUpdate from "./CycloneDXUpdate";

const ShowActions = () => {
    const cyclonedx = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "first_issued", order: "DESC" }}
                    storeKey="cyclonedx.list"
                />
                {update_permission(cyclonedx) && <CycloneDXUpdate />}
                {delete_permission(cyclonedx) && <DeleteWithConfirmButton />}
            </Stack>
        </TopToolbar>
    );
};

const CycloneDXComponent = () => {
    return (
        <WithRecord
            render={(cyclonedx) => (
                <Box width={"100%"}>
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                                <cyclonedxs.icon />
                                &nbsp;&nbsp;Exported CycloneDX document
                            </Typography>
                            {cyclonedx?.product_data?.name && (
                                <Labeled>
                                    <ProductReferenceField label="Product" />
                                </Labeled>
                            )}
                            {cyclonedx?.vulnerability_names && (
                                <Labeled>
                                    <ReferenceManyField
                                        reference="vex/cyclonedx_vulnerabilities"
                                        target="cyclonedx"
                                        label="Vulnerabilities"
                                    >
                                        <SingleFieldList linkType={false}>
                                            <ChipField source="name" />
                                        </SingleFieldList>
                                    </ReferenceManyField>
                                </Labeled>
                            )}
                            {cyclonedx?.branch_names && (
                                <Labeled>
                                    <ReferenceManyField
                                        reference="vex/cyclonedx_branches"
                                        target="cyclonedx"
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
                        <WithRecord
                            render={(cyclonedx) => (
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
                                    {cyclonedx.author && (
                                        <Labeled>
                                            <TextField source="author" />
                                        </Labeled>
                                    )}
                                    {cyclonedx.manufacturer && (
                                        <Labeled>
                                            <TextField source="manufacturer" />
                                        </Labeled>
                                    )}
                                </Stack>
                            )}
                        />
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Tracking
                            </Typography>
                            <Labeled>
                                <DateField source="first_issued" showTime={true} />
                            </Labeled>
                            <Labeled>
                                <DateField source="last_updated" showTime={true} />
                            </Labeled>
                        </Stack>
                    </Paper>
                </Box>
            )}
        />
    );
};
const CycloneDXShow = () => {
    return (
        <Show actions={<ShowActions />} component={CycloneDXComponent}>
            <Fragment />
        </Show>
    );
};

export default CycloneDXShow;
