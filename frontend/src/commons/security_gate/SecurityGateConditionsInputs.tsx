import AddIcon from "@mui/icons-material/Add";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import LinkOutlinedIcon from "@mui/icons-material/LinkOutlined";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import {
    Button,
    Chip,
    FormHelperText,
    IconButton,
    InputAdornment,
    Link,
    Paper,
    Stack,
    TextField,
    ToggleButton,
    ToggleButtonGroup,
    Typography,
} from "@mui/material";
import { Fragment } from "react";
import { BooleanInput, useResourceContext } from "react-admin";
import { useFormContext, useWatch } from "react-hook-form";

import { feature_exploit_information } from "../functions";
import { ConditionChip, OrDivider, SeverityChip, ThresholdChip } from "./SecurityGateChips";
import { SecurityGateDraftPreview } from "./SecurityGatePreview";
import {
    CONDITIONS,
    SECURITY_GATE_DOCS_URL,
    SECURITY_GATE_SEVERITIES,
    SecurityGateConditions,
    SecurityGateRule,
    SeverityMode,
    conditionSelected,
    describeRule,
    emptyRule,
    normalizeConditions,
    ruleHasCondition,
    severityMode,
    severityRules,
    thresholdSource,
    toggleCondition,
    withSeverityRules,
} from "./conditions";

const sentenceCase = { textTransform: "none" } as const;

type RuleEditorProps = {
    rules: SecurityGateRule[];
    onChange: (rules: SecurityGateRule[]) => void;
};

const RuleEditor = ({ rules, onChange }: RuleEditorProps) => {
    const replaceRule = (index: number, rule: SecurityGateRule) =>
        onChange(rules.map((existing, i) => (i === index ? rule : existing)));

    return (
        <Stack spacing={1} sx={{ alignItems: "flex-start" }}>
            {rules.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                    No conditions yet
                </Typography>
            )}
            {rules.map((rule, index) => (
                <Fragment key={index}>
                    {index > 0 && <OrDivider />}
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap", rowGap: 1 }}>
                        <ToggleButtonGroup
                            exclusive
                            size="small"
                            value={rule.operator ?? "any"}
                            onChange={(_, operator) => operator && replaceRule(index, { ...rule, operator })}
                        >
                            <ToggleButton value="any" sx={sentenceCase}>
                                Any
                            </ToggleButton>
                            <ToggleButton value="all" sx={sentenceCase}>
                                All
                            </ToggleButton>
                        </ToggleButtonGroup>
                        {CONDITIONS.map((condition) => (
                            <Fragment key={condition.key}>
                                <ConditionChip
                                    condition={condition}
                                    selected={conditionSelected(rule, condition)}
                                    disabled={condition.needsExploitInformation && !feature_exploit_information()}
                                    onClick={() => replaceRule(index, toggleCondition(rule, condition))}
                                />
                                {condition.key === "epss_min" && rule.epss_min != null && (
                                    <TextField
                                        type="number"
                                        size="small"
                                        value={rule.epss_min}
                                        onChange={(event) =>
                                            replaceRule(index, {
                                                ...rule,
                                                epss_min: event.target.value === "" ? 0 : Number(event.target.value),
                                            })
                                        }
                                        slotProps={{
                                            htmlInput: { min: 0, max: 100, step: 0.1, "aria-label": "EPSS percent" },
                                            input: { endAdornment: <InputAdornment position="end">%</InputAdornment> },
                                        }}
                                        sx={{ width: "7em" }}
                                    />
                                )}
                            </Fragment>
                        ))}
                        <IconButton
                            size="small"
                            aria-label="Remove rule"
                            onClick={() => onChange(rules.filter((_, i) => i !== index))}
                        >
                            <DeleteOutlinedIcon fontSize="small" />
                        </IconButton>
                    </Stack>
                    {!ruleHasCondition(rule) && <FormHelperText error>Select at least one condition</FormHelperText>}
                </Fragment>
            ))}
            <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => onChange([...rules, emptyRule()])}
                sx={sentenceCase}
            >
                Add rule
            </Button>
        </Stack>
    );
};

type SeverityRowProps = {
    severity: string;
    conditions: SecurityGateConditions;
    update: (conditions: SecurityGateConditions) => void;
};

const SeverityRow = ({ severity, conditions, update }: SeverityRowProps) => {
    const threshold = useWatch({ name: thresholdSource(severity) });
    const mode = severityMode(conditions, severity);

    const setMode = (next: SeverityMode) => {
        const rules = next === "inherit" ? undefined : next === "none" ? [] : [emptyRule()];
        update(withSeverityRules(conditions, severity, rules));
    };

    const summary = () => {
        if (mode === "none") {
            return <Chip size="small" variant="outlined" label="All observations" />;
        }
        if (mode === "inherit") {
            const [first, ...rest] = conditions.default;
            return (
                <Chip
                    size="small"
                    variant="outlined"
                    icon={<LinkOutlinedIcon />}
                    label={
                        first ? describeRule(first) + (rest.length ? ` +${rest.length} rules` : "") : "All observations"
                    }
                    sx={{ opacity: 0.7 }}
                />
            );
        }
        return null;
    };

    return (
        <Stack spacing={1}>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap", rowGap: 1 }}>
                <SeverityChip severity={severity} />
                <ThresholdChip threshold={threshold} />
                <ToggleButtonGroup exclusive size="small" value={mode} onChange={(_, next) => next && setMode(next)}>
                    <ToggleButton value="inherit" sx={sentenceCase}>
                        Inherit
                    </ToggleButton>
                    <ToggleButton value="custom" sx={sentenceCase}>
                        Custom
                    </ToggleButton>
                    <ToggleButton value="none" sx={sentenceCase}>
                        None
                    </ToggleButton>
                </ToggleButtonGroup>
                {summary()}
            </Stack>
            {mode === "custom" && (
                <RuleEditor
                    rules={severityRules(conditions, severity) ?? []}
                    onChange={(rules) => update(withSeverityRules(conditions, severity, rules))}
                />
            )}
        </Stack>
    );
};

const AdvancedHelperText = () => (
    <Fragment>
        Only CVEs matching the conditions count. Findings without a CVE always count.{" "}
        <Link href={SECURITY_GATE_DOCS_URL} target="_blank" rel="noreferrer">
            Learn more <OpenInNewIcon sx={{ fontSize: "inherit", verticalAlign: "middle" }} />
        </Link>
    </Fragment>
);

/** The inputs of the advanced security gate, below the thresholds of a product, product group or the settings. */
export const SecurityGateConditionsInputs = () => {
    const { setValue } = useFormContext();
    const resource = useResourceContext();
    const advanced = useWatch({ name: "security_gate_advanced" });
    const conditions = normalizeConditions(useWatch({ name: "security_gate_conditions" }));

    const update = (next: SecurityGateConditions) => setValue("security_gate_conditions", next, { shouldDirty: true });

    return (
        <Stack spacing={2} sx={{ marginTop: 1, width: "100%" }}>
            <BooleanInput source="security_gate_advanced" label="Advanced" helperText={<AdvancedHelperText />} />
            {advanced && (
                <Fragment>
                    <Paper variant="outlined" sx={{ padding: 2 }}>
                        <Typography variant="subtitle2">All severities</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", marginBottom: 1 }}>
                            Default set, used by every severity without its own rules
                        </Typography>
                        <RuleEditor
                            rules={conditions.default}
                            onChange={(rules) => update({ ...conditions, default: rules })}
                        />
                    </Paper>
                    <Paper variant="outlined" sx={{ padding: 2 }}>
                        <Typography variant="subtitle2">Per severity</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", marginBottom: 1 }}>
                            Override the default set where needed
                        </Typography>
                        <Stack spacing={1.5}>
                            {SECURITY_GATE_SEVERITIES.map((severity) => (
                                <SeverityRow
                                    key={severity}
                                    severity={severity}
                                    conditions={conditions}
                                    update={update}
                                />
                            ))}
                        </Stack>
                    </Paper>
                    {/* A product group has no observations of its own to count */}
                    {(resource === "products" || resource === "settings") && <SecurityGateDraftPreview />}
                </Fragment>
            )}
        </Stack>
    );
};
