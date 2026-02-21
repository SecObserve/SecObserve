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

import openvexs from ".";
import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";
import { delete_permission, update_permission } from "../functions";
import OpenVEXUpdate from "./OpenVEXUpdate";

const ShowActions = () => {
    const openvex = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons linkType="show" sort={{ field: "timestamp", order: "DESC" }} storeKey="openvex.list" />
                {update_permission(openvex) && <OpenVEXUpdate />}
                {delete_permission(openvex) && <DeleteWithConfirmButton />}
            </Stack>
        </TopToolbar>
    );
};

const OpenVEXComponent = () => {
    return (
        <WithRecord
            render={(openvex) => (
                <Box width={"100%"}>
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                                <openvexs.icon />
                                &nbsp;&nbsp;Exported OpenVEX document
                            </Typography>
                            {openvex?.product_data?.name && (
                                <Labeled>
                                    <ProductReferenceField label="Product" />
                                </Labeled>
                            )}
                            {openvex?.vulnerability_names && (
                                <Labeled>
                                    <ReferenceManyField
                                        reference="vex/openvex_vulnerabilities"
                                        target="openvex"
                                        label="Vulnerabilities"
                                    >
                                        <SingleFieldList linkType={false}>
                                            <ChipField source="name" />
                                        </SingleFieldList>
                                    </ReferenceManyField>
                                </Labeled>
                            )}
                            {openvex?.branch_names && (
                                <Labeled>
                                    <ReferenceManyField
                                        reference="vex/openvex_branches"
                                        target="openvex"
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
                                <TextField source="id_namespace" label="ID namespace" />
                            </Labeled>
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
                                <TextField source="author" />
                            </Labeled>
                            <Labeled>
                                <TextField source="role" />
                            </Labeled>
                        </Stack>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Tracking
                            </Typography>
                            <Labeled>
                                <DateField source="timestamp" showTime={true} />
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
const OpenVEXShow = () => {
    return (
        <Show actions={<ShowActions />} component={OpenVEXComponent}>
            <Fragment />
        </Show>
    );
};

export default OpenVEXShow;
