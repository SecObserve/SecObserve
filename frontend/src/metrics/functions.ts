import { getResolvedSettingTheme } from "../commons/user_settings/functions";

export function getGridColor() {
    if (getResolvedSettingTheme() == "dark") {
        return "#666666";
    } else {
        return "#e5e5e5";
    }
}

export function getBackgroundColor() {
    if (getResolvedSettingTheme() == "dark") {
        return "#282828";
    } else {
        return "white";
    }
}

export function getFontColor() {
    if (getResolvedSettingTheme() == "dark") {
        return "#bcbcbc";
    } else {
        return "#666666";
    }
}

export function getElevation(on_dashboard?: boolean) {
    if (on_dashboard) {
        return 1;
    }

    if (getResolvedSettingTheme() == "dark") {
        return 4;
    } else {
        return 1;
    }
}
