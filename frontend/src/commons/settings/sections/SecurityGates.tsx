import { Grid, Stack } from "@mui/material";
import {
    BooleanField,
    BooleanInput,
    FormDataConsumer,
    Labeled,
    NumberField,
    NumberInput,
    useRecordContext,
} from "react-admin";

import { validate_0_999999 } from "../../custom_validators";

export const SecurityGatesInputs = () => (
    <>
        <BooleanInput
            source="security_gate_active"
            label="Security gates active"
            helperText="Are security gates activated?"
            sx={{ marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.security_gate_active && (
                    <Grid container spacing={2} sx={{ width: "100%" }}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <NumberInput
                                    source="security_gate_threshold_critical"
                                    label="Threshold critical"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Number of critical observations that must not be exceeded"
                                    sx={{ marginBottom: 2 }}
                                />
                                <NumberInput
                                    source="security_gate_threshold_high"
                                    label="Threshold high"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Number of high observations that must not be exceeded"
                                    sx={{ marginBottom: 2 }}
                                />
                                <NumberInput
                                    source="security_gate_threshold_medium"
                                    label="Threshold medium"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Number of medium observations that must not be exceeded"
                                    sx={{ marginBottom: 2 }}
                                />
                            </Stack>
                        </Grid>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <NumberInput
                                    source="security_gate_threshold_low"
                                    label="Threshold low"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Number of low observations that must not be exceeded"
                                    sx={{ marginBottom: 2 }}
                                />
                                <NumberInput
                                    source="security_gate_threshold_none"
                                    label="Threshold none"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Number of none observations that must not be exceeded"
                                    sx={{ marginBottom: 2 }}
                                />
                                <NumberInput
                                    source="security_gate_threshold_unknown"
                                    label="Threshold unknown"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Number of unknown observations that must not be exceeded"
                                    sx={{ marginBottom: 2 }}
                                />
                            </Stack>
                        </Grid>
                    </Grid>
                )
            }
        </FormDataConsumer>
    </>
);

export const SecurityGatesFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <Labeled label="Security gates active" sx={{ marginBottom: 2 }}>
                <BooleanField source="security_gate_active" />
            </Labeled>
            {settings.security_gate_active && (
                <Grid container spacing={2} sx={{ width: "100%" }}>
                    <Grid size={3}>
                        <Stack spacing={2}>
                            <Labeled label="Threshold critical">
                                <NumberField source="security_gate_threshold_critical" />
                            </Labeled>
                            <Labeled label="Threshold high">
                                <NumberField source="security_gate_threshold_high" />
                            </Labeled>
                            <Labeled label="Threshold medium">
                                <NumberField source="security_gate_threshold_medium" />
                            </Labeled>
                        </Stack>
                    </Grid>
                    <Grid size={3}>
                        <Stack spacing={2}>
                            <Labeled label="Threshold low">
                                <NumberField source="security_gate_threshold_low" />
                            </Labeled>
                            <Labeled label="Threshold none">
                                <NumberField source="security_gate_threshold_none" />
                            </Labeled>
                            <Labeled label="Threshold unknown">
                                <NumberField source="security_gate_threshold_unknown" />
                            </Labeled>
                        </Stack>
                    </Grid>
                </Grid>
            )}
        </>
    );
};
