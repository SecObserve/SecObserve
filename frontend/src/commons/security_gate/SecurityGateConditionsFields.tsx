import LinkOutlinedIcon from "@mui/icons-material/LinkOutlined";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { Chip, Link, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import { BooleanField, Labeled, useRecordContext } from "react-admin";

import { ConditionChip, OperatorChip, OrChip, SeverityChip, ThresholdChip } from "./SecurityGateChips";
import {
    SECURITY_GATE_DOCS_URL,
    SECURITY_GATE_SEVERITIES,
    SecurityGateRule,
    conditionLabel,
    normalizeConditions,
    selectedConditions,
    severityMode,
    severityRules,
    thresholdSource,
} from "./conditions";

const RuleChips = ({ rules }: { rules: SecurityGateRule[] }) => (
    <Fragment>
        {rules.map((rule, index) => (
            <Fragment key={index}>
                {index > 0 && <OrChip />}
                <OperatorChip operator={rule.operator} />
                {selectedConditions(rule).map((condition) => (
                    <ConditionChip
                        key={condition.key}
                        condition={condition}
                        selected
                        label={conditionLabel(condition, rule)}
                    />
                ))}
            </Fragment>
        ))}
    </Fragment>
);

/** The advanced security gate of a product, product group or the settings, one row per severity. */
export const SecurityGateConditionsFields = () => {
    const record = useRecordContext();
    if (!record) {
        return null;
    }

    const conditions = normalizeConditions(record.security_gate_conditions);

    return (
        <Stack spacing={1}>
            <Labeled label="Advanced">
                <BooleanField source="security_gate_advanced" />
            </Labeled>
            {record.security_gate_advanced && (
                <Fragment>
                    {SECURITY_GATE_SEVERITIES.map((severity) => {
                        const mode = severityMode(conditions, severity);
                        const rules = severityRules(conditions, severity) ?? conditions.default;
                        return (
                            <Stack
                                key={severity}
                                direction="row"
                                spacing={1}
                                sx={{
                                    alignItems: "center",
                                    flexWrap: "wrap",
                                    rowGap: 1,
                                    opacity: mode === "inherit" ? 0.6 : 1,
                                }}
                            >
                                <SeverityChip severity={severity} />
                                <ThresholdChip threshold={record[thresholdSource(severity)]} />
                                {mode === "inherit" && (
                                    <LinkOutlinedIcon
                                        fontSize="small"
                                        color="disabled"
                                        titleAccess="Uses the default set"
                                    />
                                )}
                                {mode === "none" || rules.length === 0 ? (
                                    <Chip size="small" variant="outlined" label="All observations" />
                                ) : (
                                    <RuleChips rules={rules} />
                                )}
                            </Stack>
                        );
                    })}
                    <Typography variant="caption" color="text.secondary">
                        Findings without a CVE always count. Re-evaluated on import, assessment and daily.{" "}
                        <Link href={SECURITY_GATE_DOCS_URL} target="_blank" rel="noreferrer">
                            Learn more <OpenInNewIcon sx={{ fontSize: "inherit", verticalAlign: "middle" }} />
                        </Link>
                    </Typography>
                </Fragment>
            )}
        </Stack>
    );
};
