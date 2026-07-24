import { Box, Paper, Stack } from "@mui/material";
import { Fragment } from "react";
import { PrevNextButtons, Show, TopToolbar, WithRecord, useRecordContext } from "react-admin";

import { PERMISSION_COMPONENT_LICENSE_EDIT } from "../../access_control/types";
import ComponentShowComponent from "../../core/components/ComponentShowComponent";
import ConcludedLicense from "./ConcludedLicense";
import LicenseComponentShowAside from "./LicenseComponentShowAside";
import LicenseComponentShowLicense from "./LicenseComponentShowLicense";

const ShowActions = () => {
    const license_component = useRecordContext();

    const filter = () => {
        // eslint-disable-next-line @typescript-eslint/consistent-indexed-object-style
        const filter: { [key: string]: any } = {};
        if (license_component) {
            filter.product = Number(license_component.product);
        }
        const license_component_expand_filters = localStorage.getItem("license_component_expand_filters");
        const storedFilters = license_component_expand_filters ? JSON.parse(license_component_expand_filters) : {};
        if (storedFilters.storedFilters) {
            if (storedFilters.storedFilters.branch_name) {
                filter.branch_name_exact = storedFilters.storedFilters.branch_name;
            }
            if (storedFilters.storedFilters.effective_license_name) {
                filter.effective_license_name_exact = storedFilters.storedFilters.effective_license_name;
            }
            if (storedFilters.storedFilters.evaluation_result) {
                filter.evaluation_result = storedFilters.storedFilters.evaluation_result;
            }
        } else {
            if (
                localStorage.getItem("RaStore.license_components.embedded") === null &&
                license_component?.branch_name !== null &&
                license_component?.branch_name !== undefined &&
                license_component?.branch_name !== ""
            ) {
                filter.branch_name_exact = license_component.branch_name;
            }
        }
        return filter;
    };

    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                {license_component && (
                    <PrevNextButtons
                        filter={filter()}
                        queryOptions={{ meta: { api_resource: "license_component_ids" } }}
                        linkType="show"
                        sort={{ field: "evaluation_result", order: "ASC" }}
                        storeKey="license_components.embedded"
                    />
                )}
                {license_component?.permissions?.includes(PERMISSION_COMPONENT_LICENSE_EDIT) && <ConcludedLicense />}
            </Stack>
        </TopToolbar>
    );
};

export const LicenseComponentComponent = () => {
    return (
        <WithRecord
            render={(component) => (
                <Box sx={{ width: "100%" }}>
                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <LicenseComponentShowLicense licenseComponent={component} direction="row" />
                    </Paper>
                    <Paper sx={{ marginBottom: 1, padding: 2 }}>
                        <ComponentShowComponent component={component} icon={false} />
                    </Paper>
                </Box>
            )}
        />
    );
};

const LicenseComponentShow = () => {
    return (
        <Show actions={<ShowActions />} component={LicenseComponentComponent} aside={<LicenseComponentShowAside />}>
            <Fragment />
        </Show>
    );
};

export default LicenseComponentShow;
