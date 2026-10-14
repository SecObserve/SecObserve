import { Fragment } from "react";
import { Edit, SaveButton, SimpleForm, Toolbar, useNotify, useRedirect, useStore } from "react-admin";

import settings from ".";
import ListHeader from "../../commons/layout/ListHeader";
import { set_settings_in_local_storage } from "../functions";
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
    const notify = useNotify();
    const redirect = useRedirect();
    // In the store, so that the open sections are kept when switching to the show screen.
    const [expandedSections, setExpandedSections] = useStore<string[]>(
        "settings.expandedSections",
        ALL_SECTIONS_CLOSED
    );

    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Edit
                redirect={false}
                mutationMode="pessimistic"
                transform={transform_settings}
                mutationOptions={{
                    onSuccess: async (data: any) => {
                        // The save itself has succeeded, so a failed refresh must not hide that.
                        await set_settings_in_local_storage().catch(() => undefined);
                        notify("ra.notification.updated", { type: "info", messageArgs: { smart_count: 1 } });
                        redirect("show", "settings", data.id, data);
                    },
                }}
            >
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
