import { Grid, Stack } from "@mui/material";
import { BooleanField, BooleanInput, Labeled, NumberField, NumberInput } from "react-admin";

import { validate_1_4096 } from "../../custom_validators";

export const PasswordValidationInputs = () => (
    <Grid container spacing={2} sx={{ width: "100%" }}>
        <Grid size={3}>
            <Stack spacing={2}>
                <NumberInput
                    source="password_validator_minimum_length"
                    label="Minimum length"
                    min={1}
                    step={1}
                    validate={validate_1_4096}
                    helperText="Validates that the password is of a minimum length."
                    sx={{ marginBottom: 1 }}
                />
                <BooleanInput
                    source="password_validator_attribute_similarity"
                    label="Attribute similarity"
                    helperText="Validates that the password is sufficiently different from certain attributes of the user."
                    sx={{ marginBottom: 1 }}
                />
            </Stack>
        </Grid>
        <Grid size={3}>
            <Stack spacing={2}>
                <BooleanInput
                    source="password_validator_common_passwords"
                    label="Common passwords"
                    helperText="Validates that the password is not a common password."
                    sx={{ marginBottom: 1 }}
                />
                <BooleanInput
                    source="password_validator_not_numeric"
                    label="Not entirely numeric"
                    helperText="Validate that the password is not entirely numeric."
                    sx={{ marginBottom: 1 }}
                />
            </Stack>
        </Grid>
    </Grid>
);

export const PasswordValidationFields = () => (
    <Grid container spacing={2} sx={{ width: "100%" }}>
        <Grid size={3}>
            <Stack spacing={2}>
                <Labeled label="Minimum length">
                    <NumberField source="password_validator_minimum_length" />
                </Labeled>
                <Labeled label="Attribute similarity">
                    <BooleanField source="password_validator_attribute_similarity" />
                </Labeled>
            </Stack>
        </Grid>
        <Grid size={3}>
            <Stack spacing={2}>
                <Labeled label="Common passwords">
                    <BooleanField source="password_validator_common_passwords" />
                </Labeled>
                <Labeled label="Not entirely numeric">
                    <BooleanField source="password_validator_not_numeric" />
                </Labeled>
            </Stack>
        </Grid>
    </Grid>
);
