import { Fragment } from "react";
import { Edit, SaveButton, SimpleForm, Toolbar, useStore } from "react-admin";

import settings from ".";
import ListHeader from "../../commons/layout/ListHeader";
import SectionAccordion from "../layout/SectionAccordion";
import { SETTINGS_SECTIONS, transform_settings } from "./sections";

const CustomToolbar = () => {
    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton />
        </Toolbar>
    );
};

const SettingsEdit = () => {
    // In the store, so that the open section is kept when switching to the show screen.
    const [expandedSection, setExpandedSection] = useStore<string>("settings.expandedSection", "");

    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Edit redirect="show" mutationMode="pessimistic" transform={transform_settings}>
                <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
                    {SETTINGS_SECTIONS.map(({ label, icon, Inputs }) => (
                        <SectionAccordion
                            key={label}
                            expandedSection={expandedSection}
                            setExpandedSection={setExpandedSection}
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
