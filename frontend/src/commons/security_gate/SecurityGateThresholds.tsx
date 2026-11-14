import { Grid, Stack, formControlClasses } from "@mui/material";
import { Labeled, NumberField, NumberInput, SimpleFormIteratorClasses } from "react-admin";

import { validate_0_999999 } from "../custom_validators";
import { PriorityThresholdsField, PriorityThresholdsInput } from "./PriorityThresholds";

/** Thresholds of the settings, product groups and products: two columns of severities, then the priorities. */

const SEVERITY_COLUMNS = [
    ["critical", "high", "medium"],
    ["low", "none", "unknown"],
];

// Aligns the first row of the priority thresholds with the severity thresholds: Their Stacks remove the top margin
// of the inputs, so the first row must not have one either. The label of the priority thresholds is left out as well.
const FIRST_ROW_WITHOUT_TOP_MARGIN = {
    [`& .${SimpleFormIteratorClasses.line}:first-of-type .${formControlClasses.root}`]: { marginTop: 0 },
};

export const SecurityGateThresholdsInputs = () => (
    <Grid container spacing={2} sx={{ width: "100%" }}>
        {SEVERITY_COLUMNS.map((severities) => (
            <Grid size={3} key={severities[0]}>
                <Stack spacing={2}>
                    {severities.map((severity) => (
                        <NumberInput
                            key={severity}
                            source={`security_gate_threshold_${severity}`}
                            label={`Threshold ${severity}`}
                            min={0}
                            step={1}
                            validate={validate_0_999999}
                            helperText={`Number of ${severity} observations that must not be exceeded`}
                            sx={{ marginBottom: 2 }}
                        />
                    ))}
                </Stack>
            </Grid>
        ))}
        <Grid size={6} sx={{ paddingLeft: 4 }}>
            <PriorityThresholdsInput
                label={false}
                helperText="Thresholds per priority"
                sx={FIRST_ROW_WITHOUT_TOP_MARGIN}
            />
        </Grid>
    </Grid>
);

export const SecurityGateThresholdsFields = () => (
    <Grid container spacing={2} sx={{ width: "100%" }}>
        {SEVERITY_COLUMNS.map((severities) => (
            <Grid size={3} key={severities[0]}>
                <Stack spacing={2}>
                    {severities.map((severity) => (
                        <Labeled key={severity} label={`Threshold ${severity}`}>
                            <NumberField source={`security_gate_threshold_${severity}`} />
                        </Labeled>
                    ))}
                </Stack>
            </Grid>
        ))}
        <Grid size={6} sx={{ paddingLeft: 2 }}>
            <PriorityThresholdsField />
        </Grid>
    </Grid>
);
