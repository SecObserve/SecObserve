import { Fragment } from "react";
import { Edit, SaveButton, SimpleForm, Toolbar, useStore } from "react-admin";

import settings from ".";
import ListHeader from "../../commons/layout/ListHeader";
import ExpandCollapseButtons from "../layout/ExpandCollapseButtons";
import SectionAccordion, { ALL_SECTIONS_CLOSED } from "../layout/SectionAccordion";
import { SETTINGS_SECTIONS, transform_settings } from "./sections";

const CustomToolbar = () => {
    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton />
        </Toolbar>
    );
};

const SettingsEdit = () => {
    // In the store, so that the open sections are kept when switching to the show screen.
    const [expandedSections, setExpandedSections] = useStore<string[]>(
        "settings.expandedSections",
        ALL_SECTIONS_CLOSED
    );

    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Edit redirect="show" mutationMode="pessimistic" transform={transform_settings}>
                <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
                    <ExpandCollapseButtons
                        labels={SETTINGS_SECTIONS.map((section) => section.label)}
                        expandedSections={expandedSections}
                        setExpandedSections={setExpandedSections}
                    />
                    {SETTINGS_SECTIONS.map(({ label, icon, Inputs }) => (
                        <SectionAccordion
                            key={label}
                            expandedSections={expandedSections}
                            setExpandedSections={setExpandedSections}
                            label={label}
                            icon={icon}
                        >
                            <Inputs />
                        </SectionAccordion>
                    ))}
                </SimpleForm>
            </Edit>
        </Fragment>
    );
};

export default SettingsEdit;
