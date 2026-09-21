import { Box, Stack } from "@mui/material";
import { Fragment } from "react";
import { EditButton, Show, TopToolbar, useStore } from "react-admin";

import settings from ".";
import ListHeader from "../../commons/layout/ListHeader";
import SectionAccordion from "../layout/SectionAccordion";
import JWTSecretReset from "./JWTSecretReset";
import { SETTINGS_SECTIONS } from "./sections";

const ShowActions = () => {
    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <JWTSecretReset />
                <EditButton />
            </Stack>
        </TopToolbar>
    );
};

const SettingsShow = () => {
    // In the store, so that the open section is kept when switching to the edit screen.
    const [expandedSection, setExpandedSection] = useStore<string>("settings.expandedSection", "");

    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Show actions={<ShowActions />}>
                <Box sx={{ padding: 2, width: "100%" }}>
                    {SETTINGS_SECTIONS.map(({ label, icon, Fields }) => (
                        <SectionAccordion
                            key={label}
                            expandedSection={expandedSection}
                            setExpandedSection={setExpandedSection}
                            label={label}
                            icon={icon}
                        >
                            <Fields />
                        </SectionAccordion>
                    ))}
                </Box>
            </Show>
        </Fragment>
    );
};

export default SettingsShow;
