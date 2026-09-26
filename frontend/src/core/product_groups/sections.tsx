import AltRouteIcon from "@mui/icons-material/AltRoute";
import CleaningServicesIcon from "@mui/icons-material/CleaningServices";
import EventBusyIcon from "@mui/icons-material/EventBusy";
import GavelIcon from "@mui/icons-material/Gavel";
import NotificationsIcon from "@mui/icons-material/Notifications";
import RateReviewIcon from "@mui/icons-material/RateReview";
import SecurityIcon from "@mui/icons-material/Security";
import { ComponentType, ReactElement } from "react";

import { feature_license_management } from "../../commons/functions";
import {
    AssessmentPropagationFields,
    AssessmentPropagationInputs,
    isAssessmentPropagationVisible,
} from "./sections/AssessmentPropagation";
import { HousekeepingFields, HousekeepingInputs, isHousekeepingVisible } from "./sections/Housekeeping";
import {
    LicenseManagementFields,
    LicenseManagementInputs,
    isLicenseManagementVisible,
} from "./sections/LicenseManagement";
import { NotificationsFields, NotificationsInputs, areNotificationsVisible } from "./sections/Notifications";
import { ReviewFields, ReviewInputs, isReviewVisible } from "./sections/Review";
import {
    RiskAcceptanceExpiryFields,
    RiskAcceptanceExpiryInputs,
    isRiskAcceptanceExpiryVisible,
} from "./sections/RiskAcceptanceExpiry";
import { SecurityGateFields, SecurityGateInputs, isSecurityGateVisible } from "./sections/SecurityGate";

export type ProductGroupSection = {
    label: string;
    icon: ReactElement;
    Inputs: ComponentType;
    Fields: ComponentType;
    /** Whether the show screen has anything to show for this section. Missing means always. */
    isVisible?: (product_group: any) => boolean;
    /**
     * Whether the section can be edited at all, for sections behind a feature flag. The show screen
     * deliberately does not use this: it shows what is configured even when the feature is off.
     */
    isEditable?: () => boolean;
};

/**
 * The sections of a product group, used by the show and the edit screen alike, so that both screens
 * cannot drift apart. A new field is added to the component of its section, and a new section is
 * added here. The first block of a product group is not listed here, it is never an accordion.
 */
export const PRODUCT_GROUP_SECTIONS: ProductGroupSection[] = [
    {
        label: "Housekeeping",
        icon: <CleaningServicesIcon />,
        Inputs: HousekeepingInputs,
        Fields: HousekeepingFields,
        isVisible: isHousekeepingVisible,
    },
    {
        label: "Notifications",
        icon: <NotificationsIcon />,
        Inputs: NotificationsInputs,
        Fields: NotificationsFields,
        isVisible: areNotificationsVisible,
    },
    {
        label: "Security gate",
        icon: <SecurityIcon />,
        Inputs: SecurityGateInputs,
        Fields: SecurityGateFields,
        isVisible: isSecurityGateVisible,
    },
    {
        label: "Reviews",
        icon: <RateReviewIcon />,
        Inputs: ReviewInputs,
        Fields: ReviewFields,
        isVisible: isReviewVisible,
    },
    {
        label: "Risk acceptance expiry",
        icon: <EventBusyIcon />,
        Inputs: RiskAcceptanceExpiryInputs,
        Fields: RiskAcceptanceExpiryFields,
        isVisible: isRiskAcceptanceExpiryVisible,
    },
    {
        label: "License management",
        icon: <GavelIcon />,
        Inputs: LicenseManagementInputs,
        Fields: LicenseManagementFields,
        isVisible: isLicenseManagementVisible,
        isEditable: feature_license_management,
    },
    {
        label: "Assessment propagation (experimental)",
        icon: <AltRouteIcon />,
        Inputs: AssessmentPropagationInputs,
        Fields: AssessmentPropagationFields,
        isVisible: isAssessmentPropagationVisible,
    },
];

/** The sections of the edit and create form, in order. */
export const getProductGroupEditSections = () =>
    PRODUCT_GROUP_SECTIONS.filter((section) => section.isEditable?.() ?? true);

/** The sections the show screen has something to show for, in order. */
export const getProductGroupShowSections = (product_group: any) =>
    PRODUCT_GROUP_SECTIONS.filter((section) => section.isVisible?.(product_group) ?? true);
