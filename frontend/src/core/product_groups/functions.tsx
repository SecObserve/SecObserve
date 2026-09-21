import { Divider } from "@mui/material";
import { Fragment, useState } from "react";

import SectionAccordion from "../../commons/layout/SectionAccordion";
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
    const [expandedSection, setExpandedSection] = useState("");

    return (
        <Fragment>
            <ProductGroupBasicsInputs initialDescription={initialDescription} setDescription={setDescription} />
            <Divider flexItem sx={{ marginBottom: 2 }} />
            {getProductGroupEditSections().map(({ label, icon, Inputs }) => (
                <SectionAccordion
                    key={label}
                    expandedSection={expandedSection}
                    setExpandedSection={setExpandedSection}
                    label={label}
                    icon={icon}
                >
                    <Inputs />
                </SectionAccordion>
            ))}
        </Fragment>
    );
};
