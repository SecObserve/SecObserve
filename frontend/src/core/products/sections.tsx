import AltRouteIcon from "@mui/icons-material/AltRoute";
import BugReportIcon from "@mui/icons-material/BugReport";
import EventBusyIcon from "@mui/icons-material/EventBusy";
import GavelIcon from "@mui/icons-material/Gavel";
import NotificationsIcon from "@mui/icons-material/Notifications";
import RateReviewIcon from "@mui/icons-material/RateReview";
import RuleIcon from "@mui/icons-material/Rule";
import SecurityIcon from "@mui/icons-material/Security";
import SourceIcon from "@mui/icons-material/Source";
import TroubleshootIcon from "@mui/icons-material/Troubleshoot";
import { ComponentType, ReactElement } from "react";
import { Identifier } from "react-admin";

import { feature_license_management } from "../../commons/functions";
import {
    AssessmentPropagationFields,
    AssessmentPropagationInputs,
    isAssessmentPropagationVisible,
} from "./sections/AssessmentPropagation";
import { IssueTrackerFields, IssueTrackerInputs, isIssueTrackerVisible } from "./sections/IssueTracker";
import {
    LicenseManagementFields,
    LicenseManagementInputs,
    isLicenseManagementVisible,
} from "./sections/LicenseManagement";
import { NotificationsFields, NotificationsInputs, areNotificationsVisible } from "./sections/Notifications";
import { RepositoryFields, RepositoryInputs, isRepositoryVisible } from "./sections/Repository";
import { ReviewFields, ReviewInputs, isReviewVisible } from "./sections/Review";
import {
    RiskAcceptanceExpiryFields,
    RiskAcceptanceExpiryInputs,
    isRiskAcceptanceExpiryVisible,
} from "./sections/RiskAcceptanceExpiry";
import { RulesFields, RulesInputs } from "./sections/Rules";
import {
    SecurityGateFields,
    SecurityGateInputs,
    SecurityGateProductGroupFields,
    isSecurityGateProductGroupVisible,
    isSecurityGateVisible,
} from "./sections/SecurityGate";
import {
    VulnerabilityScanningFields,
    VulnerabilityScanningInputs,
    isVulnerabilityScanningVisible,
} from "./sections/VulnerabilityScanning";

export type ProductSectionInputsProps = {
    productGroupId?: Identifier;
};

export type ProductSection = {
    label: string;
    icon: ReactElement;
    /** Missing for sections that are only shown, never edited. */
    Inputs?: ComponentType<ProductSectionInputsProps>;
    Fields?: ComponentType;
    /** Whether the show screen has anything to show for this section. Missing means always. */
    isVisible?: (product: any) => boolean;
    /**
     * Whether the section can be edited at all, for sections behind a feature flag. The show screen
     * deliberately does not use this: it shows what is configured even when the feature is off.
     */
    isEditable?: () => boolean;
};

/**
 * The sections of a product, used by the show and the edit screen alike, so that both screens
 * cannot drift apart. A new field is added to the component of its section, and a new section is
 * added here. The first block of a product is not listed here, it is never an accordion.
 */
export const PRODUCT_SECTIONS: ProductSection[] = [
    {
        label: "Rules",
        icon: <RuleIcon />,
        Inputs: RulesInputs,
        Fields: RulesFields,
        isVisible: (product) => Boolean(product.apply_general_rules),
    },
    {
        label: "Source code repository and housekeeping",
        icon: <SourceIcon />,
        Inputs: RepositoryInputs,
        Fields: RepositoryFields,
        isVisible: isRepositoryVisible,
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
        // The security gate inherited from the product group. Its condition is mutually exclusive
        // with the one of the product's own security gate, so only one of them is ever shown.
        label: "Security gate",
        icon: <SecurityIcon />,
        Fields: SecurityGateProductGroupFields,
        isVisible: isSecurityGateProductGroupVisible,
    },
    {
        label: "Issue tracker",
        icon: <BugReportIcon />,
        Inputs: IssueTrackerInputs,
        Fields: IssueTrackerFields,
        isVisible: isIssueTrackerVisible,
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
        label: "Vulnerability scanning (OSV / VulnerableCode)",
        icon: <TroubleshootIcon />,
        Inputs: VulnerabilityScanningInputs,
        Fields: VulnerabilityScanningFields,
        isVisible: isVulnerabilityScanningVisible,
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
export const getProductEditSections = () =>
    PRODUCT_SECTIONS.filter((section) => section.Inputs && (section.isEditable?.() ?? true));

/** The sections the show screen has something to show for, in order. */
export const getProductShowSections = (product: any) =>
    PRODUCT_SECTIONS.filter((section) => section.Fields && (section.isVisible?.(product) ?? true));
