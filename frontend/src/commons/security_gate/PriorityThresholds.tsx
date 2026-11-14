import { Chip, Stack, Typography } from "@mui/material";
import { ArrayInput, ArrayInputProps, Labeled, NumberInput, SimpleFormIterator, useRecordContext } from "react-admin";

import { validate_required_0_999999, validate_required_1_99 } from "../custom_validators";

export type PriorityThreshold = { priority: number; threshold: number };

type PriorityThresholdsInputProps = Pick<ArrayInputProps, "label" | "helperText" | "sx">;

export const PriorityThresholdsInput = ({
    label = "Thresholds per priority",
    helperText,
    sx,
}: PriorityThresholdsInputProps) => (
    <ArrayInput source="security_gate_priority_thresholds" label={label} helperText={helperText} sx={sx}>
        <SimpleFormIterator inline>
            <NumberInput
                source="priority"
                label="Priority"
                min={1}
                max={99}
                step={1}
                validate={validate_required_1_99}
            />
            <NumberInput
                source="threshold"
                label="Threshold"
                min={0}
                max={999999}
                step={1}
                validate={validate_required_0_999999}
                helperText="Observations with this priority that must not be exceeded"
            />
        </SimpleFormIterator>
    </ArrayInput>
);

export const PriorityThresholdsField = () => {
    const record = useRecordContext();
    if (!record) {
        return null;
    }
    const thresholds: PriorityThreshold[] = record.security_gate_priority_thresholds ?? [];

    return (
        <Labeled label="Thresholds per priority">
            {thresholds.length === 0 ? (
                <Typography variant="body2">None</Typography>
            ) : (
                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                    {thresholds.map((item) => (
                        <Chip key={item.priority} label={`Priority ${item.priority}: ${item.threshold}`} />
                    ))}
                </Stack>
            )}
        </Labeled>
    );
};
