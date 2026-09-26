import { Divider } from "@mui/material";
import { Fragment, useState } from "react";

import ExpandCollapseButtons from "../../commons/layout/ExpandCollapseButtons";
import SectionAccordion, { ALL_SECTIONS_CLOSED } from "../../commons/layout/SectionAccordion";
import { getProductGroupEditSections } from "./sections";
import { ProductGroupBasicsInputs } from "./sections/Basics";

export type ProductGroupCreateEditComponentProps = {
    initialDescription: string;
    setDescription: (value: string) => void;
};

export const ProductGroupCreateEditComponent = ({
    initialDescription,
    setDescription,
}: ProductGroupCreateEditComponentProps) => {
    const [expandedSections, setExpandedSections] = useState<string[]>(ALL_SECTIONS_CLOSED);
    const sections = getProductGroupEditSections();

    return (
        <Fragment>
            <ProductGroupBasicsInputs initialDescription={initialDescription} setDescription={setDescription} />
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
                    <Inputs />
                </SectionAccordion>
            ))}
        </Fragment>
    );
};
