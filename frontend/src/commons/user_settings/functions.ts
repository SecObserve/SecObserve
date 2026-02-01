import { ThemeType } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";
import {
    METRICS_TIMESPAN_7_DAYS,
    METRICS_TIMESPAN_30_DAYS,
    METRICS_TIMESPAN_90_DAYS,
    METRICS_TIMESPAN_365_DAYS,
} from "../types";

export type ThemePreference = "light" | "dark" | "system";

export function getSystemPrefersDark(): boolean {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function resolveTheme(preference: ThemePreference): ThemeType {
    if (preference === "system") {
        return getSystemPrefersDark() ? "dark" : "light";
    }
    return preference;
}

export function castThemePreference(theme: string): ThemePreference {
    switch (theme) {
        case "light":
            return "light";
        case "dark":
            return "dark";
        case "system":
            return "system";
        default:
            return "light";
    }
}

export function getNextTheme(current: ThemePreference): ThemePreference {
    switch (current) {
        case "light":
            return "dark";
        case "dark":
            return "system";
        case "system":
            return "light";
        default:
            return "light";
    }
}

export async function saveSettingTheme(theme: string) {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    user.setting_theme = theme;
    localStorage.setItem("user", JSON.stringify(user));
    saveSetting({ setting_theme: theme });
}

export function getSettingTheme(): string {
    let theme = "light";
    const storage_theme = localStorage.getItem("theme");
    const user = localStorage.getItem("user");
    if (user) {
        const user_json = JSON.parse(user);
        theme = user_json.setting_theme;
    } else if (storage_theme) {
        theme = storage_theme;
    }
    return theme;
}

export function getResolvedSettingTheme(): ThemeType {
    const user_theme = getSettingTheme();
    return resolveTheme(castThemePreference(user_theme));
}

export function saveSettingListSize(list_size: string) {
    saveSetting({ setting_list_size: list_size });
}

type ListSize = "small" | "medium" | undefined;

export function getSettingListSize(): ListSize {
    let list_size: ListSize = "medium";

    const user = localStorage.getItem("user");
    if (user) {
        const user_json = JSON.parse(user);
        list_size = user_json.setting_list_size as ListSize;
    }

    return list_size;
}

export function saveSettingPackageInfoPreference(package_info_preference: string) {
    saveSetting({ setting_package_info_preference: package_info_preference });
}

type PackageInfoPreference = "open/source/insights" | "ecosyste.ms" | undefined;

export function getSettingPackageInfoPreference(): PackageInfoPreference {
    let package_info_preference: PackageInfoPreference = "open/source/insights";

    const user = localStorage.getItem("user");
    if (user) {
        const user_json = JSON.parse(user);
        package_info_preference = user_json.setting_package_info_preference as PackageInfoPreference;
    }

    return package_info_preference;
}

export function getTheme(): ThemeType {
    const setting_theme = getSettingTheme() as ThemePreference;
    return resolveTheme(setting_theme);
}

export async function saveSettingsMetricsTimespan(setting_metrics_timespan: string) {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    user.setting_metrics_timespan = setting_metrics_timespan;
    localStorage.setItem("user", JSON.stringify(user));
    saveSetting({ setting_metrics_timespan: setting_metrics_timespan });
}

export function getSettingMetricsTimespan(): string {
    let setting_metrics_timespan = METRICS_TIMESPAN_7_DAYS;
    const user = localStorage.getItem("user");
    if (user) {
        const user_json = JSON.parse(user);
        setting_metrics_timespan = user_json.setting_metrics_timespan;
    }

    return setting_metrics_timespan;
}

export function getSettingsMetricsTimespanInDays(): number {
    switch (getSettingMetricsTimespan()) {
        case METRICS_TIMESPAN_7_DAYS:
            return 7;
        case METRICS_TIMESPAN_30_DAYS:
            return 30;
        case METRICS_TIMESPAN_90_DAYS:
            return 90;
        case METRICS_TIMESPAN_365_DAYS:
            return 365;
        default:
            return 7; // Default to Week
    }
}

function saveSetting(setting: any) {
    const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/users/my_settings/";

    httpClient(url, {
        method: "PATCH",
        body: JSON.stringify(setting),
    })
        .then((response) => {
            localStorage.setItem("user", JSON.stringify(response.json));
        })
        .catch((error) => {
            console.warn(error.message);
        });
}
