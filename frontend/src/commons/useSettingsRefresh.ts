import { useEffect } from "react";

import { IntervalHooks } from "./IntervalHooks";
import { set_settings_in_local_storage } from "./functions";

const SETTINGS_REFRESH_INTERVAL = 5 * 60 * 1000;

function refresh_settings() {
    // A failed refresh keeps the current settings, it is tried again with the next one
    set_settings_in_local_storage().catch((error: Error) => {
        console.warn("Cannot refresh settings: ", error.message);
    });
}

/** Keeps the settings of this session up to date with changes made by other users. */
export function useSettingsRefresh(): void {
    IntervalHooks.useDispatch(refresh_settings, SETTINGS_REFRESH_INTERVAL);

    useEffect(() => {
        refresh_settings();
        window.addEventListener("focus", refresh_settings);
        return () => window.removeEventListener("focus", refresh_settings);
    }, []);
}
