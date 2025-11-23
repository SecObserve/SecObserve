import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Chip, Stack, Typography } from "@mui/material";
import { Fragment } from "react";

import { getElevation } from "../../metrics/functions";
import ProductRuleApprovalList from "../../rules/product_rules/ProductRuleApprovalList";
import ObservationLogApprovalList from "../observation_logs/ObservationLogApprovalList";
import ObservationsReviewList from "../observations/ObservationReviewList";

type ProductReviewsProps = {
    product: any;
};

const get_chip_color = (value: number) => {
    if (value > 0) {
        return "secondary";
    }
    return "default";
};

const ProductReviews = ({ product }: ProductReviewsProps) => {
    return (
        <Fragment>
            <Accordion
                elevation={getElevation()}
                defaultExpanded={
                    product.observation_reviews > 0 &&
                    product.observation_log_approvals == 0 &&
                    product.product_rule_approvals == 0
                }
                disableGutters
            >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Stack direction="row" sx={{ display: "flex", alignItems: "center" }}>
                        <Typography variant="h6">Observations to be reviewed:</Typography>&nbsp;&nbsp;&nbsp;
                        <Chip label={product.observation_reviews} color={get_chip_color(product.observation_reviews)} />
                    </Stack>
                </AccordionSummary>
                <AccordionDetails>
                    <ObservationsReviewList product={product} />
                </AccordionDetails>
            </Accordion>
            {(product.assessments_need_approval || product.product_group_assessments_need_approval) && (
                <Accordion
                    elevation={getElevation()}
                    sx={{ marginTop: 2 }}
                    defaultExpanded={
                        product.observation_log_approvals > 0 &&
                        product.observation_reviews == 0 &&
                        product.product_rule_approvals == 0
                    }
                    disableGutters
                >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Stack direction="row" sx={{ display: "flex", alignItems: "center" }}>
                            <Typography variant="h6">Assessments to be approved:</Typography>&nbsp;&nbsp;&nbsp;
                            <Chip
                                label={product.observation_log_approvals}
                                color={get_chip_color(product.observation_log_approvals)}
                            />
                        </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                        <ObservationLogApprovalList product={product} />
                    </AccordionDetails>
                </Accordion>
            )}
            {(product.product_rules_need_approval || product.product_group_product_rules_need_approval) && (
                <Accordion
                    elevation={getElevation()}
                    sx={{ marginTop: 2 }}
                    defaultExpanded={
                        product.product_rule_approvals > 0 &&
                        product.observation_log_approvals == 0 &&
                        product.observation_reviews == 0
                    }
                    disableGutters
                >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Stack direction="row" sx={{ display: "flex", alignItems: "center" }}>
                            <Typography variant="h6">Product rules to be approved:</Typography>&nbsp;&nbsp;&nbsp;
                            <Chip
                                label={product.product_rule_approvals}
                                color={get_chip_color(product.product_rule_approvals)}
                            />
                        </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                        <ProductRuleApprovalList product={product} />
                    </AccordionDetails>
                </Accordion>
            )}
        </Fragment>
    );
};

export default ProductReviews;
