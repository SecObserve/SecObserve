import { Divider } from "@mui/material";
import { Fragment, useState } from "react";

import ExpandCollapseButtons from "../../commons/layout/ExpandCollapseButtons";
import SectionAccordion, { ALL_SECTIONS_CLOSED } from "../../commons/layout/SectionAccordion";
import { getProductGroupShowSections } from "./sections";
import { ProductGroupBasicsFields } from "./sections/Basics";

type ProductGroupShowProductGroupProps = {
    product_group: any;
};

const ProductGroupShowProductGroup = ({ product_group }: ProductGroupShowProductGroupProps) => {
    const [expandedSections, setExpandedSections] = useState<string[]>(ALL_SECTIONS_CLOSED);
    const sections = getProductGroupShowSections(product_group);

    return (
        <Fragment>
            <ProductGroupBasicsFields />
            <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
            <ExpandCollapseButtons
                labels={sections.map((section) => section.label)}
                expandedSections={expandedSections}
                setExpandedSections={setExpandedSections}
            />
            {sections.map(({ label, icon, Fields }) => (
                <SectionAccordion
                    key={label}
                    expandedSections={expandedSections}
                    setExpandedSections={setExpandedSections}
                    label={label}
                    icon={icon}
                >
                    <Fields />
                </SectionAccordion>
            ))}
        </Fragment>
    );
};

export default ProductGroupShowProductGroup;
