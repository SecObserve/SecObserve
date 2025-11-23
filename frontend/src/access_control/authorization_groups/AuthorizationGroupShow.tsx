import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Box, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    EditButton,
    Labeled,
    PrevNextButtons,
    Show,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import authorization_groups from ".";
import { is_superuser } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import UserProductAuthorizationGroupMemberEmbeddedList from "../../core/product_authorization_group_members/UserProductAuthorizationGroupMemberEmbeddedList";
import AuthorizationGroupMemberEmbeddedList from "../authorization_group_members/AuthorizationGroupMemberEmbeddedList";

const ShowActions = () => {
    const authorization_group = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "name", order: "ASC" }}
                    filterDefaultValues={{ is_active: true }}
                    storeKey="authorization_groups.embedded"
                />
                {(authorization_group?.is_manager || is_superuser()) && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const AuthorizationGroupComponent = () => {
    const { classes } = useStyles();

    return (
        <WithRecord
            render={(authorization_group) => (
                <Box width={"100%"} sx={{ marginBottom: 2 }}>
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                            <authorization_groups.icon />
                            &nbsp;&nbsp;Authorization Group
                        </Typography>
                        <Stack spacing={1}>
                            <Labeled label="Name">
                                <TextField source="name" className={classes.fontBigBold} />
                            </Labeled>
                            {authorization_group.oidc_group && (
                                <Labeled label="OIDC group">
                                    <TextField source="oidc_group" />
                                </Labeled>
                            )}
                        </Stack>
                    </Paper>
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Users
                        </Typography>
                        <AuthorizationGroupMemberEmbeddedList authorization_group={authorization_group} />
                    </Paper>
                    {authorization_group.has_product_group_members && (
                        <Accordion sx={{ marginBottom: 2, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">Product Groups</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <UserProductAuthorizationGroupMemberEmbeddedList
                                    authorization_group={authorization_group}
                                    is_product_group={true}
                                />
                            </AccordionDetails>
                        </Accordion>
                    )}
                    {authorization_group.has_product_members && (
                        <Accordion sx={{ marginBottom: 2, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">Products</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <UserProductAuthorizationGroupMemberEmbeddedList
                                    authorization_group={authorization_group}
                                    is_product_group={false}
                                />
                            </AccordionDetails>
                        </Accordion>
                    )}
                </Box>
            )}
        />
    );
};

const AuthorizationGroupShow = () => {
    return (
        <Show actions={<ShowActions />} component={AuthorizationGroupComponent}>
            <Fragment />
        </Show>
    );
};

export default AuthorizationGroupShow;
