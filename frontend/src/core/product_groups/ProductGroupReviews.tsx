import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Chip, Stack, Typography } from "@mui/material";
import { Fragment, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { getElevation } from "../../metrics/functions";
import ProductRuleApprovalList from "../../rules/product_rules/ProductRuleApprovalList";
import ObservationLogApprovalList from "../observation_logs/ObservationLogApprovalList";

type ProductGroupReviewsProps = {
    product_group: any;
};

const get_chip_color = (value: number) => {
    if (value > 0) {
        return "secondary";
    }
    return "default";
};

const ProductGroupReviews = ({ product_group: product_group }: ProductGroupReviewsProps) => {
    const location = useLocation();
    const expand_request = (location.state as { expand?: string } | null)?.expand;

    const [assessmentsExpanded, setAssessmentsExpanded] = useState(
        expand_request === "assessments" ||
            (product_group.observation_log_approvals > 0 && product_group.product_rule_approvals == 0)
    );
    const [productRulesExpanded, setProductRulesExpanded] = useState(
        expand_request === "product_rules" ||
            (product_group.product_rule_approvals > 0 && product_group.observation_log_approvals == 0)
    );

    useEffect(() => {
        if (expand_request === "assessments") {
            setAssessmentsExpanded(true);
        }
        if (expand_request === "product_rules") {
            setProductRulesExpanded(true);
        }
    }, [expand_request, location.key]);

    return (
        <Fragment>
            {(product_group.assessments_need_approval || product_group.observation_log_approvals > 0) && (
                <Accordion
                    elevation={getElevation()}
                    sx={{ marginTop: 2 }}
                    expanded={assessmentsExpanded}
                    onChange={(_, expanded) => setAssessmentsExpanded(expanded)}
                    disableGutters
                >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Stack direction="row" sx={{ display: "flex", alignItems: "center" }}>
                            <Typography variant="h6">Assessments to be approved:</Typography>&nbsp;&nbsp;&nbsp;
                            <Chip
                                label={product_group.observation_log_approvals}
                                color={get_chip_color(product_group.observation_log_approvals)}
                            />
                        </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                        <ObservationLogApprovalList product={product_group} is_product_group={true} />
                    </AccordionDetails>
                </Accordion>
            )}
            {(product_group.product_rules_need_approval || product_group.product_group_product_rules_need_approval) && (
                <Accordion
                    elevation={getElevation()}
                    sx={{ marginTop: 2 }}
                    expanded={productRulesExpanded}
                    onChange={(_, expanded) => setProductRulesExpanded(expanded)}
                >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Stack direction="row" sx={{ display: "flex", alignItems: "center" }}>
                            <Typography variant="h6">Product rules to be approved:</Typography>&nbsp;&nbsp;&nbsp;
                            <Chip
                                label={product_group.product_rule_approvals}
                                color={get_chip_color(product_group.product_rule_approvals)}
                            />
                        </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                        <ProductRuleApprovalList product={product_group} />
                    </AccordionDetails>
                </Accordion>
            )}
        </Fragment>
    );
};

export default ProductGroupReviews;
