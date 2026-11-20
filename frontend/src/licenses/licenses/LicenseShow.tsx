import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import { BooleanField, Labeled, PrevNextButtons, Show, TextField, TopToolbar, WithRecord } from "react-admin";

import licenses from ".";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { useStyles } from "../../commons/layout/themes";
import LicenseGroupEmbeddedList from "../license_groups/LicenseGroupEmbeddedList";
import LicensePolicyEmbeddedList from "../license_policies/LicensePolicyEmbeddedList";

const ShowActions = () => {
    return (
        <TopToolbar>
            <PrevNextButtons linkType="show" sort={{ field: "spdx_id", order: "ASC" }} storeKey="licenses.embedded" />
        </TopToolbar>
    );
};

const UrlList = ({ urls }: { urls: string[] }) => (
    <Stack spacing={0.5}>
        {urls.map((url) => (
            <TextUrlField key={url} text={url} url={url} new_tab={true} />
        ))}
    </Stack>
);

const LicenseComponent = () => {
    const { classes } = useStyles();

    return (
        <WithRecord
            render={(license) => (
                <Stack spacing={2} sx={{ marginBottom: 1, width: "100%" }}>
                    <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: "stretch" }}>
                        <Paper sx={{ flex: 1, minWidth: 0, padding: 2 }}>
                            <Stack spacing={1}>
                                <Typography
                                    variant="h6"
                                    sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}
                                >
                                    <licenses.icon />
                                    &nbsp;&nbsp;SPDX License
                                </Typography>
                                <Labeled label="SPDX Id">
                                    <TextField source="spdx_id" className={classes.fontBigBold} />
                                </Labeled>
                                <Labeled>
                                    <TextField source="name" />
                                </Labeled>
                                <Labeled label="OSI approved">
                                    <BooleanField source="is_osi_approved" />
                                </Labeled>
                                <Labeled label="Deprecated">
                                    <BooleanField source="is_deprecated" />
                                </Labeled>
                                <WithRecord
                                    render={(license) => (
                                        <Labeled label="Reference">
                                            <TextUrlField
                                                text={license.reference}
                                                url={license.reference}
                                                label="Reference"
                                                new_tab={true}
                                            />
                                        </Labeled>
                                    )}
                                />
                            </Stack>{" "}
                        </Paper>
                        {license.scancode_key && (
                            <Paper sx={{ flex: 1, minWidth: 0, padding: 2 }}>
                                <Stack spacing={1}>
                                    <Typography
                                        variant="h6"
                                        sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}
                                    >
                                        <licenses.icon />
                                        &nbsp;&nbsp;ScanCode LicenseDB
                                    </Typography>
                                    {license.scancode_category && (
                                        <Labeled label="Category">
                                            <TextField source="scancode_category" />
                                        </Labeled>
                                    )}
                                    {license.scancode_owner && (
                                        <Labeled label="Owner">
                                            <TextField source="scancode_owner" />
                                        </Labeled>
                                    )}
                                    {license.scancode_homepage_url && (
                                        <Labeled label="Homepage">
                                            <UrlList urls={[license.scancode_homepage_url]} />
                                        </Labeled>
                                    )}
                                    {license.scancode_text_urls?.length > 0 && (
                                        <Labeled label="License text">
                                            <UrlList urls={license.scancode_text_urls} />
                                        </Labeled>
                                    )}
                                    {license.scancode_osi_url && (
                                        <Labeled label="OSI">
                                            <UrlList urls={[license.scancode_osi_url]} />
                                        </Labeled>
                                    )}
                                    {license.scancode_faq_url && (
                                        <Labeled label="FAQ">
                                            <UrlList urls={[license.scancode_faq_url]} />
                                        </Labeled>
                                    )}
                                    <Typography variant="caption">
                                        Source:{" "}
                                        <TextUrlField
                                            text="ScanCode LicenseDB"
                                            url={
                                                "https://scancode-licensedb.aboutcode.org/" +
                                                encodeURIComponent(license.scancode_key) +
                                                ".html"
                                            }
                                            new_tab={true}
                                        />
                                        &nbsp;&nbsp; (CC-BY-4.0)
                                    </Typography>
                                </Stack>
                            </Paper>
                        )}
                    </Stack>
                    {license.is_in_license_group && (
                        <Accordion sx={{ marginBottom: 0, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">License Groups containing this license</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <WithRecord render={(license) => <LicenseGroupEmbeddedList license={license} />} />
                            </AccordionDetails>
                        </Accordion>
                    )}
                    {license.is_in_license_policy && (
                        <Accordion sx={{ marginBottom: 0, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">License Policies containing this license</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <WithRecord
                                    render={(license) => (
                                        <LicensePolicyEmbeddedList license={license} license_group={null} />
                                    )}
                                />
                            </AccordionDetails>
                        </Accordion>
                    )}
                </Stack>
            )}
        />
    );
};

const LicenseShow = () => {
    return (
        <Show actions={<ShowActions />} component={LicenseComponent}>
            <Fragment />
        </Show>
    );
};

export default LicenseShow;
