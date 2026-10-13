export type ThemeName = "light" | "dark";

declare global {
    interface Window {
        restServer: any;
    }
}

export const VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX = "CSAF/OpenVEX";
export const VEX_JUSTIFICATION_TYPE_CYCLONEDX = "CycloneDX";

export const VEX_JUSTIFICATION_TYPE_CHOICES = [
    { id: VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX, name: VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX },
    { id: VEX_JUSTIFICATION_TYPE_CYCLONEDX, name: VEX_JUSTIFICATION_TYPE_CYCLONEDX },
];

export const DATE_FORMAT_BROWSER = "BROWSER";
export const DATE_FORMAT_ISO8601 = "ISO8601";
export const DATE_FORMAT_UK = "UK";
export const DATE_FORMAT_US = "US";
export const DATE_FORMAT_DOTTED = "DOTTED";

export const DATE_FORMAT_CHOICES = [
    { id: DATE_FORMAT_BROWSER, name: "Browser locale" },
    { id: DATE_FORMAT_ISO8601, name: "ISO 8601 (2024-12-31 23:59:59)" },
    { id: DATE_FORMAT_UK, name: "UK (31/12/2024, 23:59:59)" },
    { id: DATE_FORMAT_US, name: "US (12/31/2024, 11:59:59 PM)" },
    { id: DATE_FORMAT_DOTTED, name: "Dotted (31.12.2024, 23:59:59)" },
];

export const METRICS_TIMESPAN_7_DAYS = "Week";
export const METRICS_TIMESPAN_30_DAYS = "Month";
export const METRICS_TIMESPAN_90_DAYS = "Quarter";
export const METRICS_TIMESPAN_365_DAYS = "Year";

export const METRICS_TIMESPAN_CHOICES = [
    { id: METRICS_TIMESPAN_7_DAYS, name: METRICS_TIMESPAN_7_DAYS },
    { id: METRICS_TIMESPAN_30_DAYS, name: METRICS_TIMESPAN_30_DAYS },
    { id: METRICS_TIMESPAN_90_DAYS, name: METRICS_TIMESPAN_90_DAYS },
    { id: METRICS_TIMESPAN_365_DAYS, name: METRICS_TIMESPAN_365_DAYS },
];
