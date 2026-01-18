import { PackageURL } from "packageurl-js";
import { SortPayload } from "ra-core";

import { httpClient } from "../commons/ra-data-django-rest-framework";
import {
    OBSERVATION_SEVERITY_CRITICAL,
    OBSERVATION_SEVERITY_HIGH,
    OBSERVATION_SEVERITY_LOW,
    OBSERVATION_SEVERITY_MEDIUM,
    OBSERVATION_SEVERITY_NONE,
    OBSERVATION_SEVERITY_UNKNOWN,
    OBSERVATION_STATUS_FALSE_POSITIVE,
    OBSERVATION_STATUS_NOT_AFFECTED,
    OBSERVATION_STATUS_NOT_SECURITY,
} from "../core/types";
import {
    EVALUATION_RESULT_ALLOWED,
    EVALUATION_RESULT_FORBIDDEN,
    EVALUATION_RESULT_IGNORED,
    EVALUATION_RESULT_REVIEW_REQUIRED,
    EVALUATION_RESULT_UNKNOWN,
} from "../licenses/types";
import { getSettingPackageInfoPreference, getSettingTheme } from "./user_settings/functions";

export function getErrorMessage(error: unknown) {
    if (error instanceof Error) return error.message;
    return String(error);
}

export function getIconAndFontColor() {
    if (getSettingTheme() == "dark") {
        return "white";
    } else {
        return "black";
    }
}

export function get_severity_color(severity: string): string {
    let backgroundColor = "transparent";
    switch (severity) {
        case OBSERVATION_SEVERITY_UNKNOWN:
            backgroundColor = "#00B4F0";
            break;
        case OBSERVATION_SEVERITY_NONE:
            backgroundColor = "#53aa33";
            break;
        case OBSERVATION_SEVERITY_LOW:
            backgroundColor = "#ffcb0d";
            break;
        case OBSERVATION_SEVERITY_MEDIUM:
            backgroundColor = "#f9a009";
            break;
        case OBSERVATION_SEVERITY_HIGH:
            backgroundColor = "#df3d03";
            break;
        case OBSERVATION_SEVERITY_CRITICAL:
            backgroundColor = "#cc0500";
            break;
    }
    return backgroundColor;
}

export function get_evaluation_result_color(record: any, evaluation_result: string | null): string {
    if (!evaluation_result) {
        if (record?.component_license_data) {
            evaluation_result = record.component_license_data.evaluation_result;
        } else {
            evaluation_result = record.evaluation_result;
        }
    }

    let backgroundColor = "transparent";
    switch (evaluation_result) {
        case EVALUATION_RESULT_ALLOWED:
            backgroundColor = "#53aa33";
            break;
        case EVALUATION_RESULT_FORBIDDEN:
            backgroundColor = "#df3d03";
            break;
        case EVALUATION_RESULT_REVIEW_REQUIRED:
            backgroundColor = "#f9a009";
            break;
        case EVALUATION_RESULT_UNKNOWN:
            backgroundColor = "#424242";
            break;
        case EVALUATION_RESULT_IGNORED:
            backgroundColor = "#424242";
            break;
    }
    return backgroundColor;
}

export function get_cwe_url(cwe: number): string {
    return "https://cwe.mitre.org/data/definitions/" + cwe + ".html";
}

export function get_cvss3_url(cvss_vector: string): string {
    if (cvss_vector.startsWith("CVSS:3.0/")) {
        return "https://www.first.org/cvss/calculator/3.0#" + cvss_vector;
    } else if (cvss_vector.startsWith("CVSS:3.1/")) {
        return "https://www.first.org/cvss/calculator/3.1#" + cvss_vector;
    }
    return "";
}

export function get_cvss4_url(cvss_vector: string): string {
    if (cvss_vector.startsWith("CVSS:4.0/")) {
        return "https://www.first.org/cvss/calculator/4.0#" + cvss_vector;
    }
    return "";
}

export function get_component_purl_url(component_purl: string): string | null {
    if (component_purl === "") {
        return null;
    }

    try {
        const purl = PackageURL.fromString(component_purl);

        if (purl.type === undefined || purl.name === undefined) {
            return null;
        }

        let package_info_preference = getSettingPackageInfoPreference();
        package_info_preference ??= "open/source/insights";

        let namespace_separator = "/";
        if (purl.type === "maven") {
            namespace_separator = ":";
        }

        let component_purl_url: string | null = null;

        if (package_info_preference === "open/source/insights") {
            component_purl_url = get_purl_url_deps_dev(
                purl.type,
                purl.namespace,
                purl.name,
                purl.version,
                namespace_separator
            );
        }

        component_purl_url ??= get_purl_url_ecosyste_ms(purl.type, purl.namespace, purl.name, namespace_separator);

        return component_purl_url;
    } catch (e: unknown) {
        console.warn("PURL " + component_purl + " is not valid: " + getErrorMessage(e));
        return null;
    }
}

function get_purl_url_deps_dev(
    purl_type: string,
    purl_namespace: string | undefined,
    purl_name: string,
    purl_version: string | undefined,
    namespace_separator: string
): string | null {
    let purl_url: string | null = null;

    const typeArray: string[] = ["cargo", "golang", "maven", "npm", "nuget", "pypi"];
    if (purl_type !== null && purl_name !== null && typeArray.includes(purl_type)) {
        let deps_dev_type = purl_type;
        if (purl_type === "golang") {
            deps_dev_type = "go";
        }

        purl_url = "https://deps.dev/" + deps_dev_type + "/";
        if (purl_namespace !== undefined) {
            purl_url += encodeURIComponent(purl_namespace) + encodeURIComponent(namespace_separator);
        }
        purl_url += encodeURIComponent(purl_name);
        if (purl_version !== undefined) {
            purl_url += "/" + purl_version;
        }
    }

    return purl_url;
}

function get_purl_url_ecosyste_ms(
    purl_type: string,
    purl_namespace: string | undefined,
    purl_name: string,
    namespace_separator: string
): string | null {
    let purl_url: string | null = null;

    const types: Record<string, string> = {
        npm: "npmjs.org",
        golang: "proxy.golang.org",
        nuget: "nuget.org",
        maven: "repo1.maven.org",
        pypi: "pypi.org",
        composer: "packagist.org",
        gem: "rubygems.org",
        cargo: "crates.io",
        cocoapods: "cocoapods.org",
        cpan: "cpan.org",
        cran: "cran.r-project.org",
        hackage: "hackage.haskell.org",
    };

    if (Object.keys(types).includes(purl_type)) {
        const ecosystems_type = types[purl_type]; // eslint-disable-line security/detect-object-injection

        purl_url = "https://packages.ecosyste.ms/registries/" + ecosystems_type + "/packages/";
        if (purl_namespace !== undefined) {
            purl_url += encodeURIComponent(purl_namespace) + encodeURIComponent(namespace_separator);
        }
        purl_url += encodeURIComponent(purl_name);
    }

    return purl_url;
}

const rtf = new Intl.RelativeTimeFormat("en", {
    localeMatcher: "best fit",
    numeric: "auto", // change to "always" if you want 1 day ago/from now
    // instead of yesterday/tomorrow
    style: "long",
});

export const humanReadableDate = (date: string | undefined) => {
    if (date === undefined) {
        return "";
    }

    const today = new Date().setHours(23, 59, 59, 999);
    const diffInMs = Date.parse(date).valueOf() - today.valueOf();
    const diffInDays = diffInMs / (1000 * 60 * 60 * 24);
    return rtf.format(Math.trunc(diffInDays), "day").replace(" ago", "");
};

export function set_settings_in_local_storage() {
    httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/status/settings/").then((response) => {
        localStorage.setItem("settings", JSON.stringify(response.json));
    });
}

export const feature_email = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_vex_position = features.indexOf("feature_email");
        return feature_vex_position !== -1;
    } catch {
        return false;
    }
};

export const feature_vex_enabled = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_vex_position = features.indexOf("feature_vex");
        return feature_vex_position !== -1;
    } catch {
        return false;
    }
};

export function settings_risk_acceptance_expiry_date(): string | null {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const risk_acceptance_expiry_days = settings.risk_acceptance_expiry_days ?? null;
        if (risk_acceptance_expiry_days === null) {
            return null;
        }
        const date = new Date();
        date.setDate(date.getDate() + risk_acceptance_expiry_days);
        return date.toISOString().split("T")[0];
    } catch {
        return null;
    }
}

export function settings_vex_justification_style(): string | null {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const vex_justification_style = settings.vex_justification_style ?? null;
        if (vex_justification_style === null) {
            return null;
        }
        return vex_justification_style;
    } catch {
        return null;
    }
}

export const feature_general_rules_need_approval_enabled = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_general_rules_need_approval = features.indexOf("feature_general_rules_need_approval");
        return feature_general_rules_need_approval !== -1;
    } catch {
        return false;
    }
};

export const feature_license_management = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_vex_position = features.indexOf("feature_license_management");
        return feature_vex_position !== -1;
    } catch {
        return false;
    }
};

export const feature_automatic_api_import = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_vex_position = features.indexOf("feature_automatic_api_import");
        return feature_vex_position !== -1;
    } catch {
        return false;
    }
};

export const feature_automatic_osv_scanning = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_vex_position = features.indexOf("feature_automatic_osv_scanning");
        return feature_vex_position !== -1;
    } catch {
        return false;
    }
};

export const feature_exploit_information = () => {
    try {
        const settings = JSON.parse(localStorage.getItem("settings") ?? "{}");
        const features = settings.features ?? [];
        const feature_vex_position = features.indexOf("feature_exploit_information");
        return feature_vex_position !== -1;
    } catch {
        return false;
    }
};

export const justificationIsEnabledForStatus = (status: string) => {
    const vex_enabled = feature_vex_enabled();
    const justification_recommended_for_status = [
        OBSERVATION_STATUS_NOT_AFFECTED,
        OBSERVATION_STATUS_NOT_SECURITY,
        OBSERVATION_STATUS_FALSE_POSITIVE,
    ].includes(status);
    return vex_enabled && justification_recommended_for_status;
};

export const is_superuser = () => {
    const user = localStorage.getItem("user");
    return user && JSON.parse(user).is_superuser;
};

export const is_external = () => {
    const user = localStorage.getItem("user");
    return user && JSON.parse(user).is_external;
};

export function has_attribute(attribute: string, data: any, sort: SortPayload | undefined) {
    if (sort?.field === attribute) {
        return true;
    }

    if (!data || !Array.isArray(data)) {
        return false;
    }

    return data.some((entry: any) => {
        if (!entry) return false;

        // Handle nested attributes (e.g., "product_data.name")
        if (attribute.includes(".")) {
            const parts = attribute.split(".");
            let value: any = entry;
            for (const part of parts) {
                if (value && typeof value === "object") {
                    value = value[part]; // eslint-disable-line security/detect-object-injection
                } else {
                    value = undefined;
                    break;
                }
            }
            return value !== null && value !== undefined && value !== "";
        } else {
            const value = entry[attribute]; // eslint-disable-line security/detect-object-injection
            return value !== null && value !== undefined && value !== "";
        }
    });
}
