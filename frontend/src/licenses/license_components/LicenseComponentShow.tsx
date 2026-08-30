import { Box, Paper, Stack } from "@mui/material";
import { Fragment } from "react";
import { PrevNextButtons, Show, TopToolbar, WithRecord, useRecordContext } from "react-admin";

import { PERMISSION_COMPONENT_LICENSE_EDIT } from "../../access_control/types";
import ConcludedLicense from "./ConcludedLicense";
import LicenseComponentShowAside from "./LicenseComponentShowAside";
import LicenseComponentShowComponent from "./LicenseComponentShowComponent";
import LicenseComponentShowLicense from "./LicenseComponentShowLicense";
import { IDENTIFIER_LICENSE_COMPONENT_COMPONENT_LIST } from "./functions";

const ShowActions = () => {
    const license_component = useRecordContext();

    const embeddedListFilter = () => {
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

    let filter = null;
    let storeKey = null;

    if (license_component) {
        if (
            localStorage.getItem(IDENTIFIER_LICENSE_COMPONENT_COMPONENT_LIST) === "true" &&
            license_component.component
        ) {
            filter = { component: Number(license_component.component) };
            storeKey = "component_license_components.embedded";
        } else {
            filter = embeddedListFilter();
            storeKey = "license_components.embedded";
        }
    }

    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                {filter && storeKey && (
                    <PrevNextButtons
                        filter={filter}
                        queryOptions={{ meta: { api_resource: "license_component_ids" } }}
                        linkType="show"
                        sort={{ field: "evaluation_result", order: "ASC" }}
                        storeKey={storeKey}
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
                        <LicenseComponentShowComponent component={component} icon={false} />
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
