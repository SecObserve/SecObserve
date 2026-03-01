import { Box, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Identifier, Labeled, TextField, WithRecord, useNotify, useRecordContext } from "react-admin";

import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import LicenseComponentShowLicense from "../../licenses/license_components/LicenseComponentShowLicense";

const ComponentShowAside = () => {
    const [licenseComponent, setLicenseComponent] = useState(undefined);
    const notify = useNotify();
    const component = useRecordContext();

    useEffect(() => {
        if (component) {
            get_data(component.id);
        }
    }, [component]); // eslint-disable-line react-hooks/exhaustive-deps

    function get_data(component_id: Identifier) {
        httpClient(
            window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_components/for_component/?component=" + component_id,
            {
                method: "GET",
            }
        )
            .then((result) => {
                if (result.status === 200) {
                    setLicenseComponent(result.json);
                } else {
                    setLicenseComponent(undefined);
                }
            })
            .catch((error) => {
                setLicenseComponent(undefined);
                if (error !== undefined) {
                    notify(error.message, {
                        type: "warning",
                    });
                } else {
                    notify("Error while loading License Component", {
                        type: "warning",
                    });
                }
            });
    }

    return (
        <Box width={"33%"} marginLeft={2}>
            <MetaData />
            {licenseComponent && <License licenseComponent={licenseComponent} />}
        </Box>
    );
};

const MetaData = () => {
    return (
        <WithRecord
            render={(component) => (
                <Paper sx={{ marginBottom: 2, padding: 2 }}>
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Metadata
                    </Typography>
                    <Stack spacing={1}>
                        <Labeled label="Product">
                            <ProductReferenceField />
                        </Labeled>
                        {component.branch_name && (
                            <Labeled label="Branch">
                                <TextField source="branch_name" />
                            </Labeled>
                        )}
                        {component.origin_service_name && (
                            <Labeled label="Service">
                                <TextField source="origin_service_name" />
                            </Labeled>
                        )}
                    </Stack>
                </Paper>
            )}
        />
    );
};

type LicenseProps = {
    licenseComponent?: any;
};

const License = ({ licenseComponent }: LicenseProps) => {
    return (
        <Paper sx={{ marginBottom: 2, padding: 2 }}>
            <LicenseComponentShowLicense licenseComponent={licenseComponent} direction="column" />
        </Paper>
    );
};

export default ComponentShowAside;
