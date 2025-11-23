import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Box, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    DateField,
    EditButton,
    Labeled,
    PrevNextButtons,
    Show,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import users from ".";
import { is_superuser } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import UserProductMemberEmbeddedList from "../../core/product_members/UserProductMemberEmbeddedList";
import ApiTokenCreate from "../api_tokens/ApiTokenCreate";
import ApiTokenEmbeddedList from "../api_tokens/ApiTokenEmbeddedList";
import AuthorizationGroupEmbeddedList from "../authorization_groups/AuthorizationGroupEmbeddedList";
import UserChangePassword from "./UserChangePassword";

const ShowActions = () => {
    const current_user = localStorage.getItem("user");
    const user = useRecordContext();

    let filter = null;
    let storeKey = null;

    if (localStorage.getItem("userembeddedlist")) {
        filter = {};
        storeKey = "users.embedded";
    }
    if (localStorage.getItem("useragembeddedlist")) {
        filter = { authorization_group: localStorage.getItem("useragembeddedlist.authorization_group") };
        storeKey = "users.agembedded";
    }

    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                {filter && storeKey && (
                    <PrevNextButtons
                        linkType="show"
                        filter={filter}
                        sort={{ field: "username", order: "ASC" }}
                        filterDefaultValues={{ is_active: true }}
                        storeKey={storeKey}
                    />
                )}
                {user &&
                    !user.is_oidc_user &&
                    (is_superuser() || (current_user && user && JSON.parse(current_user).id == user.id)) && (
                        <UserChangePassword />
                    )}
                {is_superuser() && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const UserComponent = () => {
    const { classes } = useStyles();
    const current_user = localStorage.getItem("user");
    const current_user_id = current_user ? JSON.parse(current_user).id : 0;

    const showFullInformation = (user: any) => {
        return is_superuser() || current_user_id == user.id;
    };

    const userWidth = (user: any) => {
        return showFullInformation(user) ? "50%" : "100%";
    };

    return (
        <WithRecord
            render={(user) => (
                <Box width={"100%"} sx={{ marginBottom: 2 }}>
                    <Stack direction="row" spacing={2} sx={{ marginBottom: 1 }}>
                        <Stack sx={{ width: userWidth(user) }}>
                            <Paper sx={{ marginBottom: 1, padding: 2, height: "100%" }}>
                                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                                    <users.icon />
                                    &nbsp;&nbsp;User
                                </Typography>
                                <Stack spacing={1}>
                                    <Labeled label="Username">
                                        <TextField source="username" className={classes.fontBigBold} />
                                    </Labeled>
                                    <Labeled label="Full name">
                                        <TextField source="full_name" />
                                    </Labeled>
                                    {user.first_name && (
                                        <Labeled label="First name">
                                            <TextField source="first_name" />
                                        </Labeled>
                                    )}
                                    {user.last_name && (
                                        <Labeled label="Last name">
                                            <TextField source="last_name" />
                                        </Labeled>
                                    )}
                                    {user.email && (
                                        <Labeled label="Email">
                                            <TextField source="email" />
                                        </Labeled>
                                    )}
                                    {user.date_joined && (
                                        <Labeled label="Created">
                                            <DateField source="date_joined" showTime />
                                        </Labeled>
                                    )}
                                    {user.has_password != undefined && (
                                        <Labeled label="Has password">
                                            <BooleanField source="has_password" />
                                        </Labeled>
                                    )}
                                    {user.is_oidc_user != undefined && (
                                        <Labeled label="OIDC user">
                                            <BooleanField source="is_oidc_user" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Paper>
                        </Stack>
                        {showFullInformation(user) && (
                            <Stack sx={{ width: "50%" }}>
                                <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                        Permissions
                                    </Typography>
                                    <Stack spacing={1}>
                                        <Labeled label="Active">
                                            <BooleanField source="is_active" />
                                        </Labeled>
                                        <Labeled label="External">
                                            <BooleanField source="is_external" />
                                        </Labeled>
                                        <Labeled label="Superuser">
                                            <BooleanField source="is_superuser" />
                                        </Labeled>
                                    </Stack>
                                </Paper>
                                <Paper sx={{ marginBottom: 1, padding: 2, width: "100%", height: "100%" }}>
                                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                        Settings
                                    </Typography>
                                    <Stack spacing={1}>
                                        {user.setting_theme && (
                                            <Labeled label="Theme">
                                                <TextField source="setting_theme" />
                                            </Labeled>
                                        )}
                                        {user.setting_list_size && (
                                            <Labeled label="List size">
                                                <TextField source="setting_list_size" />
                                            </Labeled>
                                        )}
                                        {user.setting_package_info_preference && (
                                            <Labeled label="Package information preference">
                                                <TextField source="setting_package_info_preference" />
                                            </Labeled>
                                        )}
                                    </Stack>
                                </Paper>
                            </Stack>
                        )}
                    </Stack>
                    {showFullInformation(user) && (user.has_api_tokens || current_user_id === user.id) && (
                        <Accordion sx={{ marginBottom: 2, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">API Token</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                {current_user_id === user.id && (
                                    <Box sx={{ marginBottom: 2 }}>
                                        <ApiTokenCreate type="user" user={user} />
                                    </Box>
                                )}
                                <ApiTokenEmbeddedList type="user" user={user} />
                            </AccordionDetails>
                        </Accordion>
                    )}
                    {showFullInformation(user) && user.has_authorization_groups && (
                        <Accordion sx={{ marginBottom: 2, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">Authorization Groups</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <AuthorizationGroupEmbeddedList user={user} />
                            </AccordionDetails>
                        </Accordion>
                    )}
                    {showFullInformation(user) && user.has_product_group_members && (
                        <Accordion sx={{ marginBottom: 2, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">Product Groups</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <UserProductMemberEmbeddedList user={user} is_product_group={true} />
                            </AccordionDetails>
                        </Accordion>
                    )}
                    {showFullInformation(user) && user.has_product_members && (
                        <Accordion sx={{ marginBottom: 2, padding: 0 }} disableGutters>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="h6">Products</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <UserProductMemberEmbeddedList user={user} is_product_group={false} />
                            </AccordionDetails>
                        </Accordion>
                    )}
                </Box>
            )}
        />
    );
};

const UserShow = () => {
    return (
        <Show actions={<ShowActions />} component={UserComponent}>
            <Fragment />
        </Show>
    );
};

export default UserShow;
