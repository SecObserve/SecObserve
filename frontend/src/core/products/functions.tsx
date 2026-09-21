import { Divider } from "@mui/material";
import { Fragment, useState } from "react";
import { Identifier } from "react-admin";

import ExpandCollapseButtons from "../../commons/layout/ExpandCollapseButtons";
import SectionAccordion, { ALL_SECTIONS_CLOSED } from "../../commons/layout/SectionAccordion";
import { transform_product_group_and_product } from "../functions";
import { getProductEditSections } from "./sections";
import { ProductBasicsInputs } from "./sections/Basics";

export const transform = (data: any, description: string) => {
    data = transform_product_group_and_product(data, description);

    data.purl ??= "";
    data.cpe23 ??= "";
    data.repository_prefix ??= "";

    data.issue_tracker_type ??= "";
    data.issue_tracker_base_url ??= "";
    data.issue_tracker_api_key ??= "";
    data.issue_tracker_project_id ??= "";
    data.issue_tracker_labels ??= "";
    data.issue_tracker_username ??= "";
    data.issue_tracker_issue_type ??= "";
    data.issue_tracker_status_closed ??= "";
    data.issue_tracker_minimum_severity ??= "";

    if (!data.osv_enabled) {
        data.osv_linux_distribution = "";
        data.osv_linux_release = "";
        data.automatic_osv_scanning_enabled = false;
    }
    if (!data.vulnerablecode_enabled) {
        data.automatic_vulnerablecode_scanning_enabled = false;
    }
    data.osv_linux_distribution ??= "";
    data.osv_linux_release ??= "";

    return data;
};

export type ProductCreateEditComponentProps = {
    initialDescription: string;
    setDescription: (value: string) => void;
    productGroupId?: Identifier;
};

export const ProductCreateEditComponent = ({
    initialDescription,
    setDescription,
    productGroupId,
}: ProductCreateEditComponentProps) => {
    const [expandedSections, setExpandedSections] = useState<string[]>(ALL_SECTIONS_CLOSED);
    const sections = getProductEditSections();

    return (
        <Fragment>
            <ProductBasicsInputs
                initialDescription={initialDescription}
                setDescription={setDescription}
                productGroupId={productGroupId}
            />
            <Divider flexItem sx={{ marginBottom: 2 }} />
            <ExpandCollapseButtons
                labels={sections.map((section) => section.label)}
                expandedSections={expandedSections}
                setExpandedSections={setExpandedSections}
            />
            {sections.map(({ label, icon, Inputs }) => (
                <SectionAccordion
                    key={label}
                    expandedSections={expandedSections}
                    setExpandedSections={setExpandedSections}
                    label={label}
                    icon={icon}
                >
                    {Inputs && <Inputs productGroupId={productGroupId} />}
                </SectionAccordion>
            ))}
        </Fragment>
    );
};
