import { Divider } from "@mui/material";
import { Fragment, useState } from "react";

import SectionAccordion from "../../commons/layout/SectionAccordion";
import { getProductGroupShowSections } from "./sections";
import { ProductGroupBasicsFields } from "./sections/Basics";

type ProductGroupShowProductGroupProps = {
    product_group: any;
};

const ProductGroupShowProductGroup = ({ product_group }: ProductGroupShowProductGroupProps) => {
    const [expandedSection, setExpandedSection] = useState("");

    return (
        <Fragment>
            <ProductGroupBasicsFields />
            <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
            {getProductGroupShowSections(product_group).map(({ label, icon, Fields }) => (
                <SectionAccordion
                    key={label}
                    expandedSection={expandedSection}
                    setExpandedSection={setExpandedSection}
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
