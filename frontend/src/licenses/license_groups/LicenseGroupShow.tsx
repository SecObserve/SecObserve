import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    EditButton,
    Labeled,
    PrevNextButtons,
    Show,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import license_groups from ".";
import MarkdownField from "../../commons/custom_fields/MarkdownField";
import { is_external, is_superuser } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import LicenseGroupAuthorizationGroupMemberEmbeddedList from "../license_group_authorization_group_members/LicenseGroupAuthorizationGroupMemberEmbeddedList";
import LicenseGroupLicenseEmbeddedList from "../license_group_licenses/LicenseGroupLicenseEmbeddedList";
import LicenseGroupMemberEmbeddedList from "../license_group_members/LicenseGroupMemberEmbeddedList";
import LicensePolicyEmbeddedList from "../license_policies/LicensePolicyEmbeddedList";
import LicenseGroupCopy from "./LicenseGroupCopy";

const ShowActions = () => {
    const license_group = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "name", order: "ASC" }}
                    storeKey="licensegroups.embedded"
                />
                {license_group && (!is_external() || is_superuser()) && (
                    <LicenseGroupCopy license_group={license_group} />
                )}
                {(license_group?.is_manager || is_superuser()) && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const LicenseGroupComponent = () => {
    const { classes } = useStyles();

    return (
        <WithRecord
            render={(license_group) => (
                <Stack spacing={2} sx={{ marginBottom: 1, width: "100%" }}>
                    <Paper sx={{ marginBottom: 1, padding: 2 }}>
                        <Stack spacing={1}>
                            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                                <license_groups.icon />
                                &nbsp;&nbsp;License Group
                            </Typography>
                            <Labeled>
                                <TextField source="name" className={classes.fontBigBold} />
                            </Labeled>
                            <Labeled>
                                <MarkdownField content={license_group.description} label="Description" />
                            </Labeled>
                            <Labeled label="Public">
                                <BooleanField source="is_public" />
                            </Labeled>
                        </Stack>
                    </Paper>
                    <Paper sx={{ marginBottom: 1, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Licenses
                        </Typography>
                        <LicenseGroupLicenseEmbeddedList license_group={license_group} />
                    </Paper>
                    {license_group.is_in_license_policy && (
                        <Accordion sx={{ marginBottom: 0, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">License Policies containing this license group</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <LicensePolicyEmbeddedList license={null} license_group={license_group} />
                            </AccordionDetails>
                        </Accordion>
                    )}
                    <Accordion sx={{ marginBottom: 0, padding: 0 }} disableGutters>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Users</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <LicenseGroupMemberEmbeddedList license_group={license_group} />
                        </AccordionDetails>
                    </Accordion>
                    <Accordion sx={{ marginBottom: 0, padding: 0 }} disableGutters>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="h6">Authorization Groups</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <LicenseGroupAuthorizationGroupMemberEmbeddedList license_group={license_group} />
                        </AccordionDetails>
                    </Accordion>
                </Stack>
            )}
        />
    );
};

const LicenseGroupShow = () => {
    return (
        <Show actions={<ShowActions />} component={LicenseGroupComponent}>
            <Fragment />
        </Show>
    );
};

export default LicenseGroupShow;
