import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import SettingsBrightnessIcon from "@mui/icons-material/SettingsBrightness";
import { IconButton, Tooltip } from "@mui/material";
import { useEffect, useState } from "react";
import { useTheme } from "react-admin";

import {
    ThemePreference,
    getNextTheme,
    getSettingTheme,
    resolveTheme,
    saveSettingTheme,
} from "../../commons/user_settings/functions";

const ToggleThemeButton = () => {
    const [, setTheme] = useTheme();
    const [preference, setPreference] = useState<ThemePreference>(getSettingTheme() as ThemePreference);

    useEffect(() => {
        const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const handleChange = () => {
            if (preference === "system") {
                setTheme(resolveTheme("system"));
            }
        };

        mediaQuery.addEventListener("change", handleChange);
        return () => mediaQuery.removeEventListener("change", handleChange);
    }, [preference, setTheme]);

    const toggleTheme = () => {
        const nextTheme = getNextTheme(preference);
        const resolvedTheme = resolveTheme(nextTheme);

        localStorage.setItem("theme", nextTheme);
        saveSettingTheme(nextTheme);
        setPreference(nextTheme);
        setTheme(resolvedTheme);
    };

    const tooltipTitle = () => {
        switch (preference) {
            case "light":
                return "Light mode";
            case "dark":
                return "Dark mode";
            case "system":
                return "System mode";
            default:
                return "Light mode";
        }
    };

    const resolvedTheme = resolveTheme(preference);
    const isDark = resolvedTheme === "dark";
    const iconColor = isDark ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.54)";

    const ThemeIcon = () => {
        switch (preference) {
            case "light":
                return <LightModeIcon style={{ color: iconColor }} />;
            case "dark":
                return <DarkModeIcon style={{ color: iconColor }} />;
            case "system":
                return <SettingsBrightnessIcon style={{ color: iconColor }} />;
            default:
                return <LightModeIcon style={{ color: iconColor }} />;
        }
    };

    return (
        <Tooltip title={tooltipTitle()}>
            <IconButton onClick={toggleTheme}>
                <ThemeIcon />
            </IconButton>
        </Tooltip>
    );
};

export default ToggleThemeButton;
