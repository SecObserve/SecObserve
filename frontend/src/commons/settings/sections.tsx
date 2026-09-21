import CleaningServicesIcon from "@mui/icons-material/CleaningServices";
import LockIcon from "@mui/icons-material/Lock";
import NotificationsIcon from "@mui/icons-material/Notifications";
import PasswordIcon from "@mui/icons-material/Password";
import ScheduleIcon from "@mui/icons-material/Schedule";
import SecurityIcon from "@mui/icons-material/Security";
import ToggleOnIcon from "@mui/icons-material/ToggleOn";
import { ComponentType, ReactElement } from "react";

import { AuthenticationFields, AuthenticationInputs, transformAuthentication } from "./sections/Authentication";
import { BackgroundTasksFields, BackgroundTasksInputs } from "./sections/BackgroundTasks";
import {
    BranchHousekeepingFields,
    BranchHousekeepingInputs,
    transformBranchHousekeeping,
} from "./sections/BranchHousekeeping";
import { FeaturesFields, FeaturesInputs, transformFeatures } from "./sections/Features";
import { NotificationsFields, NotificationsInputs, transformNotifications } from "./sections/Notifications";
import { PasswordValidationFields, PasswordValidationInputs } from "./sections/PasswordValidation";
import { SecurityGatesFields, SecurityGatesInputs } from "./sections/SecurityGates";

export type SettingsSection = {
    label: string;
    icon: ReactElement;
    Inputs: ComponentType;
    Fields: ComponentType;
    /** Amends the data before it is sent, for fields the backend does not accept as null. */
    transform?: (data: any) => void;
};

/**
 * The sections of the settings, used by SettingsShow and SettingsEdit alike, so that both screens
 * cannot drift apart. A new setting is added to the component of its section, and a new section is
 * added here.
 */
export const SETTINGS_SECTIONS: SettingsSection[] = [
    {
        label: "Authentication",
        icon: <LockIcon />,
        Inputs: AuthenticationInputs,
        Fields: AuthenticationFields,
        transform: transformAuthentication,
    },
    {
        label: "Features",
        icon: <ToggleOnIcon />,
        Inputs: FeaturesInputs,
        Fields: FeaturesFields,
        transform: transformFeatures,
    },
    {
        label: "Housekeeping for branches",
        icon: <CleaningServicesIcon />,
        Inputs: BranchHousekeepingInputs,
        Fields: BranchHousekeepingFields,
        transform: transformBranchHousekeeping,
    },
    {
        label: "Notifications",
        icon: <NotificationsIcon />,
        Inputs: NotificationsInputs,
        Fields: NotificationsFields,
        transform: transformNotifications,
    },
    {
        label: "Security gates",
        icon: <SecurityIcon />,
        Inputs: SecurityGatesInputs,
        Fields: SecurityGatesFields,
    },
    {
        label: "Password validation",
        icon: <PasswordIcon />,
        Inputs: PasswordValidationInputs,
        Fields: PasswordValidationFields,
    },
    {
        label: "Background tasks",
        icon: <ScheduleIcon />,
        Inputs: BackgroundTasksInputs,
        Fields: BackgroundTasksFields,
    },
];

/** The transforms of all sections, so that a section owns the handling of its own fields. */
export const transform_settings = (data: any) => {
    SETTINGS_SECTIONS.forEach((section) => section.transform?.(data));
    return data;
};
