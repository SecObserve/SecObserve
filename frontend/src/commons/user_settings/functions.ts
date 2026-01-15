import { ThemeType } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";
import {
    METRICS_TIMESPAN_7_DAYS,
    METRICS_TIMESPAN_30_DAYS,
    METRICS_TIMESPAN_90_DAYS,
    METRICS_TIMESPAN_365_DAYS,
} from "../types";

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
    const setting_theme = getSettingTheme();
    if (setting_theme == "dark") {
        return "dark";
    } else {
        return "light";
    }
}

export async function saveSettingListProperties() {
    const list_settings: { key: string; value: string | null }[] = [];
    Object.keys(localStorage).forEach(function (ls_key) {
        if (ls_key.startsWith("RaStore.preferences")) {
            list_settings.push({ key: ls_key, value: localStorage.getItem(ls_key) });
        }
    });
    const list_setting_string = JSON.stringify(list_settings);
    saveSetting({ setting_list_properties: list_setting_string });
}

export function setListProperties(setting_list_properties: string) {
    if (setting_list_properties == null || setting_list_properties == "") {
        return;
    }
    const list_settings = JSON.parse(setting_list_properties);
    list_settings.forEach(function (ls: { key: string; value: string | null }) {
        if (ls.value != null) {
            localStorage.setItem(ls.key, ls.value);
        }
    });
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
