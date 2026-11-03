import { SvgIconComponent } from "@mui/icons-material";
import BuildIcon from "@mui/icons-material/Build";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import CodeIcon from "@mui/icons-material/Code";
import GppMaybeIcon from "@mui/icons-material/GppMaybe";
import PublicIcon from "@mui/icons-material/Public";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

export type SecurityGateOperator = "any" | "all";

export interface SecurityGateRule {
    operator?: SecurityGateOperator;
    known_exploited?: boolean;
    exploit_tooling?: boolean;
    proof_of_concept?: boolean;
    epss_min?: number | null;
    network_vector?: boolean;
    fix_available?: boolean;
}

export interface SecurityGateConditions {
    default: SecurityGateRule[];
    severities: Record<string, SecurityGateRule[]>;
}

export type SecurityGatePreviewRow = {
    severity: string;
    threshold: number;
    active: number;
    counted: number;
    passed: boolean;
};

export type ConditionKey = Exclude<keyof SecurityGateRule, "operator">;

export type Condition = {
    key: ConditionKey;
    label: string;
    hint: string;
    icon: SvgIconComponent;
    /** Read from the exploit information import, which can be switched off in the settings. */
    needsExploitInformation?: boolean;
};

export const CONDITIONS: Condition[] = [
    {
        key: "known_exploited",
        label: "Known exploited",
        hint: "CISA KEV or VulnCheck KEV",
        icon: GppMaybeIcon,
        needsExploitInformation: true,
    },
    {
        key: "exploit_tooling",
        label: "Exploit tooling",
        hint: "Metasploit, Nuclei or Exploit-DB",
        icon: BuildIcon,
        needsExploitInformation: true,
    },
    {
        key: "proof_of_concept",
        label: "Proof of concept",
        hint: "PoC published on GitHub",
        icon: CodeIcon,
        needsExploitInformation: true,
    },
    { key: "epss_min", label: "EPSS ≥", hint: "EPSS score in percent, at least", icon: TrendingUpIcon },
    { key: "network_vector", label: "Network vector", hint: "CVSS AV:N, PR:N, UI:N", icon: PublicIcon },
    { key: "fix_available", label: "Fix available", hint: "A fixed version exists", icon: CheckCircleOutlinedIcon },
];

export const SECURITY_GATE_SEVERITIES = ["Critical", "High", "Medium", "Low", "None", "Unknown"];

export const SECURITY_GATE_DOCS_URL =
    "https://secobserve.github.io/SecObserve/usage/security_gates/#advanced-security-gate";

/** A threshold from this value on is shown as "Never fails". */
export const NEVER_FAILS_THRESHOLD = 99999;

export const DEFAULT_EPSS_MIN = 10;

export const thresholdSource = (severity: string) => `security_gate_threshold_${severity.toLowerCase()}`;

export const emptyRule = (): SecurityGateRule => ({ operator: "any" });

/** Tolerates null and {} from the API, so that every consumer sees both keys. */
export const normalizeConditions = (value: any): SecurityGateConditions => ({
    default: Array.isArray(value?.default) ? value.default : [],
    severities: value?.severities && typeof value.severities === "object" ? value.severities : {},
});

export const conditionSelected = (rule: SecurityGateRule, condition: Condition): boolean =>
    condition.key === "epss_min" ? rule.epss_min != null : Boolean(rule[condition.key]);

export const toggleCondition = (rule: SecurityGateRule, condition: Condition): SecurityGateRule => {
    if (condition.key === "epss_min") {
        return { ...rule, epss_min: rule.epss_min == null ? DEFAULT_EPSS_MIN : null };
    }
    return { ...rule, [condition.key]: !conditionSelected(rule, condition) };
};

export const ruleHasCondition = (rule: SecurityGateRule): boolean =>
    CONDITIONS.some((condition) => conditionSelected(rule, condition));

export const selectedConditions = (rule: SecurityGateRule): Condition[] =>
    CONDITIONS.filter((condition) => conditionSelected(rule, condition));

export const conditionLabel = (condition: Condition, rule: SecurityGateRule): string =>
    condition.key === "epss_min" ? `EPSS ≥ ${rule.epss_min} %` : condition.label;

/** One line for a rule, like "Any of Known exploited, EPSS ≥ 10 %". */
export const describeRule = (rule: SecurityGateRule): string => {
    const labels = selectedConditions(rule).map((condition) => conditionLabel(condition, rule));
    if (labels.length === 0) {
        return "No condition";
    }
    const operator = rule.operator === "all" ? "All of" : "Any of";
    return `${operator} ${labels.join(", ")}`;
};

export type SeverityMode = "inherit" | "custom" | "none";

/** The rules of a severity's own set, undefined when it inherits the default set. */
export const severityRules = (conditions: SecurityGateConditions, severity: string): SecurityGateRule[] | undefined =>
    Object.entries(conditions.severities).find(([key]) => key === severity)?.[1];

/** Absent means inherit, an empty list means every observation counts. */
export const severityMode = (conditions: SecurityGateConditions, severity: string): SeverityMode => {
    const rules = severityRules(conditions, severity);
    if (rules === undefined) {
        return "inherit";
    }
    return rules.length === 0 ? "none" : "custom";
};

/** Replaces a severity's own set, undefined lets it inherit the default set again. */
export const withSeverityRules = (
    conditions: SecurityGateConditions,
    severity: string,
    rules: SecurityGateRule[] | undefined
): SecurityGateConditions => {
    const others = Object.entries(conditions.severities).filter(([key]) => key !== severity);
    const entries = rules === undefined ? others : [...others, [severity, rules] as const];
    return { ...conditions, severities: Object.fromEntries(entries) };
};

/** Drops rules without a condition before the data is sent; untouched null values stay null. */
export const cleanSecurityGateConditions = (data: any) => {
    if (data.security_gate_conditions == null) {
        return;
    }
    const conditions = normalizeConditions(data.security_gate_conditions);
    data.security_gate_conditions = {
        default: conditions.default.filter(ruleHasCondition),
        severities: Object.fromEntries(
            Object.entries(conditions.severities).map(([severity, rules]) => [severity, rules.filter(ruleHasCondition)])
        ),
    };
};
