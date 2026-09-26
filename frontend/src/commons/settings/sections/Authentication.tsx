import { Grid } from "@mui/material";
import {
    BooleanField,
    BooleanInput,
    Labeled,
    NumberField,
    NumberInput,
    TextField,
    useRecordContext,
} from "react-admin";

import { validate_0_999999, validate_255 } from "../../custom_validators";
import { TextInputWide } from "../../layout/themes";

/** The backend does not accept null for these fields, they have to be sent as an empty string. */
export const transformAuthentication = (data: any) => {
    data.internal_users ??= "";
};

export const AuthenticationInputs = () => (
    <>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={4}>
                <NumberInput
                    autoFocus
                    source="jwt_validity_duration_user"
                    label="JWT validity duration user (hours)"
                    min={0}
                    step={1}
                    validate={validate_0_999999}
                    helperText="Validity duration of JWT tokens for regular users in hours"
                    sx={{ marginBottom: 2 }}
                />
            </Grid>
            <Grid size={4}>
                <NumberInput
                    source="jwt_validity_duration_superuser"
                    label="JWT validity duration superuser (hours)"
                    min={0}
                    step={1}
                    validate={validate_0_999999}
                    helperText="Validity duration of JWT tokens for superusers in hours"
                    sx={{ marginBottom: 2 }}
                />
            </Grid>
        </Grid>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={4}>
                <TextInputWide
                    source="internal_users"
                    label="Internal users"
                    validate={validate_255}
                    helperText="Comma separated list of email regular expressions to identify internal users"
                    sx={{ marginBottom: 2 }}
                />
            </Grid>
            <Grid size={4}>
                <BooleanInput
                    source="oidc_strict_audience"
                    label="OIDC strict audience"
                    helperText="Require the audience claim to be a single string matching the client id. Disable if the OIDC provider issues a list of audiences."
                    sx={{ marginBottom: 2 }}
                />
            </Grid>
        </Grid>
        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={4}>
                <NumberInput
                    source="oidc_clock_skew"
                    label="OIDC clock skew (seconds)"
                    min={0}
                    step={1}
                    validate={validate_0_999999}
                    helperText="Time margin in seconds for checks of issued at, not before and expiration of OIDC tokens"
                    sx={{ marginBottom: 2 }}
                />
            </Grid>
            <Grid size={4}>
                <NumberInput
                    source="oidc_api_token_max_authentication_age"
                    label="OIDC API token max authentication age (minutes)"
                    min={0}
                    step={1}
                    validate={validate_0_999999}
                    helperText="Maximum age of the OIDC authentication to create or revoke a user API token, 0 disables the check"
                    sx={{ marginBottom: 2 }}
                />
            </Grid>
        </Grid>
    </>
);

export const AuthenticationFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={4}>
                    <Labeled label="JWT validity duration user (hours)">
                        <NumberField source="jwt_validity_duration_user" />
                    </Labeled>
                </Grid>
                <Grid size={4}>
                    <Labeled label="JWT validity duration superuser (hours)">
                        <NumberField source="jwt_validity_duration_superuser" />
                    </Labeled>
                </Grid>
            </Grid>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={4}>
                    {settings.internal_users && (
                        <Labeled label="Internal users">
                            <TextField source="internal_users" />
                        </Labeled>
                    )}
                </Grid>
                <Grid size={4}>
                    <Labeled label="OIDC strict audience">
                        <BooleanField source="oidc_strict_audience" />
                    </Labeled>
                </Grid>
            </Grid>
            <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
                <Grid size={4}>
                    <Labeled label="OIDC clock skew (seconds)">
                        <NumberField source="oidc_clock_skew" />
                    </Labeled>
                </Grid>
                <Grid size={4}>
                    <Labeled label="OIDC API token max authentication age (minutes)">
                        <NumberField source="oidc_api_token_max_authentication_age" />
                    </Labeled>
                </Grid>
            </Grid>
        </>
    );
};
