import { Box, Stack } from "@mui/material";
import { Fragment } from "react";
import { EditButton, Show, TopToolbar, useStore } from "react-admin";

import settings from ".";
import ListHeader from "../../commons/layout/ListHeader";
import ExpandCollapseButtons from "../layout/ExpandCollapseButtons";
import SectionAccordion, { ALL_SECTIONS_CLOSED } from "../layout/SectionAccordion";
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
    // In the store, so that the open sections are kept when switching to the edit screen.
    const [expandedSections, setExpandedSections] = useStore<string[]>(
        "settings.expandedSections",
        ALL_SECTIONS_CLOSED
    );

    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Show actions={<ShowActions />}>
                <Box sx={{ padding: 2, width: "100%" }}>
                    <ExpandCollapseButtons
                        labels={SETTINGS_SECTIONS.map((section) => section.label)}
                        expandedSections={expandedSections}
                        setExpandedSections={setExpandedSections}
                    />
                    {SETTINGS_SECTIONS.map(({ label, icon, Fields }) => (
                        <SectionAccordion
                            key={label}
                            expandedSections={expandedSections}
                            setExpandedSections={setExpandedSections}
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
