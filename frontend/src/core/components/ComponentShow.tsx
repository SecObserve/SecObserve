import { Box, Paper, Typography } from "@mui/material";
import { Fragment } from "react";
import { PrevNextButtons, Show, TopToolbar, WithRecord } from "react-admin";

import ObservationsComponentList from "../observations/ObservationComponentList";
import ComponentShowAside from "./ComponentShowAside";
import ComponentShowComponent from "./ComponentShowComponent";

const ShowActions = () => {
    return (
        <TopToolbar>
            <PrevNextButtons
                linkType="show"
                sort={{ field: "component_name_version_type", order: "ASC" }}
                queryOptions={{ meta: { api_resource: "component_names" } }}
                storeKey="components.list"
            />
        </TopToolbar>
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
                    {component?.has_observations && (
                        <Paper sx={{ marginBottom: 1, padding: 2 }}>
                            <Typography variant="h6">Observations</Typography>
                            <ObservationsComponentList component={component} />
                        </Paper>
                    )}
                </Box>
            )}
        />
    );
};
const ComponentShow = () => {
    return (
        <Show actions={<ShowActions />} component={ComponentComponent} aside={<ComponentShowAside />}>
            <Fragment />
        </Show>
    );
};

export default ComponentShow;
