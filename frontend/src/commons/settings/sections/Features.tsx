import { Grid, Stack } from "@mui/material";
import {
    BooleanField,
    BooleanInput,
    FormDataConsumer,
    Labeled,
    NumberField,
    NumberInput,
    RadioButtonGroupInput,
    TextField,
    useRecordContext,
} from "react-admin";

import { validate_0_999999, validate_255 } from "../../custom_validators";
import { TextInputWide } from "../../layout/themes";
import { VEX_JUSTIFICATION_TYPE_CHOICES } from "../../types";

/** The backend does not accept null for these fields, they have to be sent as an empty string. */
export const transformFeatures = (data: any) => {
    data.vulnerablecode_base_url ??= "";
    data.vulnerablecode_api_key ??= "";
};

export const FeaturesInputs = () => (
    <>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={3}>
                <Stack spacing={2}>
                    <BooleanInput
                        source="feature_vex"
                        label="VEX"
                        helperText="Export and import VEX documents in various formats"
                    />
                </Stack>
            </Grid>
            <Grid size={3}>
                <Stack spacing={2}>
                    <FormDataConsumer>
                        {({ formData }) =>
                            formData.feature_vex && (
                                <RadioButtonGroupInput
                                    source="vex_justification_style"
                                    label="VEX justification style"
                                    choices={VEX_JUSTIFICATION_TYPE_CHOICES}
                                />
                            )
                        }
                    </FormDataConsumer>
                </Stack>
            </Grid>
        </Grid>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={3}>
                <Stack spacing={2}>
                    <BooleanInput
                        source="feature_disable_user_login"
                        label="Disable user login"
                        helperText="Do not show user and password fields if OIDC login is enabled"
                    />
                    <BooleanInput source="feature_license_management" label="Enable license management" />
                    <BooleanInput source="feature_automatic_osv_scanning" label="Enable automatic OSV scanning" />
                    <BooleanInput
                        source="feature_automatic_vulnerablecode_scanning"
                        label="Enable automatic VulnerableCode scanning"
                    />
                </Stack>
            </Grid>
            <Grid size={3}>
                <Stack spacing={2}>
                    <BooleanInput source="feature_automatic_api_import" label="Enable automatic API imports" />
                    <BooleanInput source="feature_general_rules_need_approval" label="General rules need approval" />
                    <BooleanInput
                        source="observation_count_from_metrics"
                        label="Calculate observation count from metrics"
                    />
                    <Stack spacing={1}>
                        <TextInputWide
                            source="vulnerablecode_base_url"
                            label="VulnerableCode base URL"
                            validate={validate_255}
                        />
                        <TextInputWide
                            source="vulnerablecode_api_key"
                            label="VulnerableCode API key"
                            validate={validate_255}
                        />
                        <NumberInput
                            source="vulnerablecode_cache_ttl_hours"
                            label="VulnerableCode cache time to live (hours)"
                            min={0}
                            step={1}
                            validate={validate_0_999999}
                        />
                    </Stack>
                </Stack>
            </Grid>
        </Grid>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={3}>
                <Stack spacing={2}>
                    <BooleanInput source="feature_exploit_information" label="Enable exploit enrichment from cvss-bt" />
                </Stack>
            </Grid>
            <Grid size={3}>
                <Stack spacing={2}>
                    <FormDataConsumer>
                        {({ formData }) =>
                            formData.feature_exploit_information && (
                                <NumberInput
                                    source="exploit_information_max_age_years"
                                    label="Maximum age of CVEs for enrichment in years"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                />
                            )
                        }
                    </FormDataConsumer>
                </Stack>
            </Grid>
        </Grid>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={3}>
                <Stack spacing={2}>
                    <BooleanInput
                        source="feature_cross_scanner_deduplication"
                        label="Enable cross scanner deduplication"
                    />
                    <BooleanInput source="feature_show_product_header_chips" label="Show chips in Product header" />
                </Stack>
            </Grid>
            <Grid size={3}>
                <Stack spacing={2}>
                    <NumberInput
                        source="risk_acceptance_expiry_days"
                        label="Risk acceptance expiry (days)"
                        min={0}
                        step={1}
                        validate={validate_0_999999}
                        helperText="Days before risk acceptance expires, 0 means no expiry"
                        sx={{ marginBottom: 2 }}
                    />
                </Stack>
            </Grid>
        </Grid>
    </>
);

export const FeaturesFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="VEX">
                            <BooleanField source="feature_vex" />
                        </Labeled>
                    </Stack>
                </Grid>
                <Grid size={3}>
                    <Stack spacing={2}>
                        {settings.feature_vex && (
                            <Labeled label="VEX justification style">
                                <TextField source="vex_justification_style" />
                            </Labeled>
                        )}
                    </Stack>
                </Grid>
            </Grid>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="Disable user login">
                            <BooleanField source="feature_disable_user_login" />
                        </Labeled>
                        <Labeled label="Enable license management">
                            <BooleanField source="feature_license_management" />
                        </Labeled>
                        <Labeled label="Enable automatic OSV scanning">
                            <BooleanField source="feature_automatic_osv_scanning" />
                        </Labeled>
                        <Labeled label="Enable automatic VulnerableCode scanning">
                            <BooleanField source="feature_automatic_vulnerablecode_scanning" />
                        </Labeled>
                    </Stack>
                </Grid>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="Enable automatic API imports">
                            <BooleanField source="feature_automatic_api_import" />
                        </Labeled>
                        <Labeled label="General rules need approval">
                            <BooleanField source="feature_general_rules_need_approval" />
                        </Labeled>
                        <Labeled label="Calculate observation count from metrics">
                            <BooleanField source="observation_count_from_metrics" />
                        </Labeled>
                        <Stack spacing={1}>
                            {settings.vulnerablecode_base_url && (
                                <Labeled label="VulnerableCode base URL">
                                    <TextField source="vulnerablecode_base_url" />
                                </Labeled>
                            )}
                            {settings.vulnerablecode_api_key && (
                                <Labeled label="VulnerableCode API key">
                                    <TextField source="vulnerablecode_api_key" />
                                </Labeled>
                            )}
                            {settings.vulnerablecode_base_url && (
                                <Labeled label="VulnerableCode cache time to live (hours)">
                                    <NumberField source="vulnerablecode_cache_ttl_hours" />
                                </Labeled>
                            )}
                        </Stack>
                    </Stack>
                </Grid>
            </Grid>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="Enable exploit enrichment from cvss-bt">
                            <BooleanField source="feature_exploit_information" />
                        </Labeled>
                    </Stack>
                </Grid>
                <Grid size={3}>
                    <Stack spacing={2}>
                        {settings.feature_exploit_information && (
                            <Labeled label="Maximum age of CVEs for enrichment in years">
                                <NumberField source="exploit_information_max_age_years" />
                            </Labeled>
                        )}
                    </Stack>
                </Grid>
            </Grid>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="Enable cross scanner deduplication">
                            <BooleanField source="feature_cross_scanner_deduplication" />
                        </Labeled>
                        <Labeled label="Show chips in Product header">
                            <BooleanField source="feature_show_product_header_chips" />
                        </Labeled>
                    </Stack>
                </Grid>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="Risk acceptance expiry (days)">
                            <NumberField source="risk_acceptance_expiry_days" />
                        </Labeled>
                    </Stack>
                </Grid>
            </Grid>
        </>
    );
};
