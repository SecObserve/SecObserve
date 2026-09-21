import { Divider } from "@mui/material";
import { Fragment, useState } from "react";

import ExpandCollapseButtons from "../../commons/layout/ExpandCollapseButtons";
import SectionAccordion, { ALL_SECTIONS_CLOSED } from "../../commons/layout/SectionAccordion";
import { Product } from "../types";
import { getProductShowSections } from "./sections";
import { ProductBasicsFields } from "./sections/Basics";

type ProductShowProductProps = {
    product: Product;
};

const ProductShowProduct = ({ product }: ProductShowProductProps) => {
    const [expandedSections, setExpandedSections] = useState<string[]>(ALL_SECTIONS_CLOSED);
    const sections = getProductShowSections(product);

    return (
        <Fragment>
            <ProductBasicsFields />
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
                    {Fields && <Fields />}
                </SectionAccordion>
            ))}
        </Fragment>
    );
};

export default ProductShowProduct;
