import { Box, Paper } from "@mui/material";
import { Fragment, useEffect, useState } from "react";
import {
    Identifier,
    PrevNextButtons,
    Show,
    Tab,
    TabbedShowLayout,
    TabbedShowLayoutTabs,
    TopToolbar,
    WithRecord,
} from "react-admin";

import license_components from "../../licenses/license_components";
import ComponentLicenseComponentList from "../../licenses/license_components/ComponentLicenseComponentList";
import observations from "../observations";
import ObservationsComponentList from "../observations/ObservationComponentList";
import ComponentShowComponent from "./ComponentShowComponent";

const ShowActions = () => {
    return (
        <TopToolbar>
            <PrevNextButtons
                linkType="show"
                sort={{ field: "name_version_type", order: "ASC" }}
                queryOptions={{ meta: { api_resource: "component_names" } }}
                storeKey="components.list"
            />
        </TopToolbar>
    );
};

type ComponentTabsProps = {
    component: any;
};

// The tabs must not be rendered before the component change has been processed:
// the stored list params have to be removed before useListController is mounted,
// otherwise it reads the params of the previous component instead of the defaults.
const ComponentTabs = ({ component }: ComponentTabsProps) => {
    const [initializedComponentId, setInitializedComponentId] = useState<Identifier | null>(null);

    useEffect(() => {
        const current_component_id = localStorage.getItem("componentshow.component");
        if (current_component_id == null || Number(current_component_id) !== Number(component.id)) {
            localStorage.removeItem("RaStore.observations.component");
            localStorage.removeItem("RaStore.component_license_components.embedded");
            localStorage.setItem("componentshow.component", String(component.id));
        }
        setInitializedComponentId(component.id);
    }, [component.id]);

    if (initializedComponentId !== component.id) {
        return <div>Loading...</div>;
    }

    return (
        <Paper sx={{ marginBottom: 1 }}>
            <TabbedShowLayout
                syncWithLocation={false}
                tabs={<TabbedShowLayoutTabs variant="scrollable" scrollButtons="auto" />}
            >
                {component?.has_observations && (
                    <Tab label="Observations" icon={<observations.icon />}>
                        <ObservationsComponentList component={component} />
                    </Tab>
                )}
                {component?.has_licenses && (
                    <Tab label="Licenses" icon={<license_components.icon />}>
                        <ComponentLicenseComponentList component={component} />
                    </Tab>
                )}
            </TabbedShowLayout>
        </Paper>
    );
};

export const ComponentComponent = () => {
    return (
        <WithRecord
            render={(component) => (
                <Box sx={{ width: "100%" }}>
                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <ComponentShowComponent component={component} icon={true} />
                    </Paper>
                    {(component?.has_observations || component?.has_licenses) && (
                        <ComponentTabs component={component} />
                    )}
                </Box>
            )}
        />
    );
};
const ComponentShow = () => {
    return (
        <Show actions={<ShowActions />} component={ComponentComponent}>
            <Fragment />
        </Show>
    );
};

export default ComponentShow;
