import { Chip, Divider, alpha } from "@mui/material";

import { get_severity_color } from "../functions";
import { Condition, NEVER_FAILS_THRESHOLD, SecurityGateOperator } from "./conditions";

export const SeverityChip = ({ severity }: { severity: string }) => (
    <Chip
        label={severity}
        size="small"
        sx={{ backgroundColor: get_severity_color(severity), color: "white", minWidth: "5em" }}
    />
);

export const ThresholdChip = ({ threshold }: { threshold: number | null | undefined }) => (
    <Chip
        size="small"
        variant="outlined"
        label={
            threshold == null ? "—" : threshold >= NEVER_FAILS_THRESHOLD ? "Never fails" : threshold.toLocaleString()
        }
        title="Threshold"
    />
);

export const OperatorChip = ({ operator }: { operator?: SecurityGateOperator }) => (
    <Chip size="small" label={operator === "all" ? "All" : "Any"} sx={{ fontWeight: "bold" }} />
);

export const OrChip = () => <Chip size="small" variant="outlined" label="Or" />;

export const OrDivider = () => (
    <Divider sx={{ width: "100%" }}>
        <OrChip />
    </Divider>
);

type ConditionChipProps = {
    condition: Condition;
    selected: boolean;
    label?: string;
    disabled?: boolean;
    onClick?: () => void;
};

export const ConditionChip = ({ condition, selected, label, disabled, onClick }: ConditionChipProps) => {
    const Icon = condition.icon;
    return (
        <Chip
            size="small"
            icon={<Icon />}
            label={label ?? condition.label}
            title={disabled ? "Exploit information is switched off in the settings" : condition.hint}
            disabled={disabled}
            onClick={onClick}
            variant={selected ? "filled" : "outlined"}
            sx={
                selected
                    ? (theme) => ({
                          backgroundColor: alpha(theme.palette.primary.main, 0.15),
                          color: theme.palette.primary.main,
                          "& .MuiChip-icon": { color: theme.palette.primary.main },
                      })
                    : undefined
            }
        />
    );
};
