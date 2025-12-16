import { Divider, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import { BooleanField, Labeled, NumberField, ReferenceField, TextField, WithRecord } from "react-admin";

import MarkdownField from "../../commons/custom_fields/MarkdownField";
import OSVLinuxDistributionField from "../../commons/custom_fields/OSVLinuxDistributionField";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { feature_email } from "../../commons/functions";
import { Product } from "../types";

type ProductShowProductProps = {
    product: Product;
};

const ProductShowProduct = ({ product }: ProductShowProductProps) => {
    return (
        <Fragment>
            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Product
            </Typography>
            <Stack spacing={1}>
                <Labeled>
                    <TextField source="name" />
                </Labeled>
                {product.description && (
                    <Labeled>
                        <MarkdownField content={product.description} label="Description" />
                    </Labeled>
                )}
                {product.product_group && (
                    <Labeled label="Product group">
                        <ReferenceField
                            source="product_group"
                            reference="product_groups"
                            queryOptions={{ meta: { api_resource: "product_group_names" } }}
                            link="show"
                            sx={{ "& a": { textDecoration: "none" } }}
                        >
                            <TextField source="name" />
                        </ReferenceField>
                    </Labeled>
                )}
                {product.purl && (
                    <Labeled label="PURL">
                        <TextField source="purl" />
                    </Labeled>
                )}
                {product.cpe23 && (
                    <Labeled label="CPE 2.3">
                        <TextField source="cpe23" />
                    </Labeled>
                )}
            </Stack>

            {product.apply_general_rules && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Rules
                    </Typography>
                    <Labeled label="Apply general rules">
                        <BooleanField source="apply_general_rules" />
                    </Labeled>
                </Fragment>
            )}

            {(product.repository_prefix ||
                product.repository_branch_housekeeping_active != null) && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Source code repository and housekeeping
                    </Typography>
                        {product.repository_prefix && (
                            <Labeled>
                                <TextField source="repository_prefix" />
                            </Labeled>
                        )}
                    {((!product.product_group && product.repository_branch_housekeeping_active != null) ||
                        (product.product_group &&
                            product.product_group_repository_branch_housekeeping_active == null &&
                            product.repository_branch_housekeeping_active != null)) && (
                        <Stack direction="row" spacing={4} sx={{ marginTop: 1 }}>
                            <Labeled label="Housekeeping">
                                <BooleanField
                                    source="repository_branch_housekeeping_active"
                                    valueLabelFalse="Disabled"
                                    valueLabelTrue="Product specific"
                                />
                            </Labeled>
                            {product.repository_branch_housekeeping_active &&
                                product.repository_branch_housekeeping_keep_inactive_days != null && (
                                    <Labeled label="Keep inactive">
                                        <NumberField source="repository_branch_housekeeping_keep_inactive_days" />
                                    </Labeled>
                                )}
                            {product.repository_branch_housekeeping_active &&
                                product.repository_branch_housekeeping_exempt_branches != "" && (
                                    <Labeled label="Exempt branches / versions">
                                        <TextField source="repository_branch_housekeeping_exempt_branches" />
                                    </Labeled>
                                )}
                        </Stack>
                    )}
                    {product.product_group && product.product_group_repository_branch_housekeeping_active != null && (
                        <Labeled label="Housekeeping (from product group)">
                            <BooleanField
                                source="product_group_repository_branch_housekeeping_active"
                                valueLabelFalse="Disabled"
                                valueLabelTrue="Product group specific"
                            />
                        </Labeled>
                    )}
                </Fragment>
            )}

            {((feature_email() && product.notification_email_to) ||
                product.notification_ms_teams_webhook ||
                product.notification_slack_webhook) && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Notifications
                    </Typography>
                    <Stack spacing={1}>
                        {feature_email() && product.notification_email_to && (
                            <Labeled label="Email">
                                <TextField source="notification_email_to" />
                            </Labeled>
                        )}
                        {product.notification_ms_teams_webhook && (
                            <Labeled label="MS Teams">
                                <TextField source="notification_ms_teams_webhook" />
                            </Labeled>
                        )}
                        {product.notification_slack_webhook && (
                            <Labeled label="Slack">
                                <TextField source="notification_slack_webhook" />
                            </Labeled>
                        )}
                    </Stack>
                </Fragment>
            )}

            {((!product.product_group && product.security_gate_active != null) ||
                (product.product_group &&
                    product.product_group_security_gate_active == null &&
                    product.security_gate_active != null)) && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Security Gate
                    </Typography>
                    <Labeled label="Security gate">
                        <BooleanField
                            source="security_gate_active"
                            valueLabelFalse="Disabled"
                            valueLabelTrue="Product specific"
                        />
                    </Labeled>
                    {product.security_gate_active && (
                        <Stack spacing={1}>
                            <Labeled>
                                <NumberField source="security_gate_threshold_critical" />
                            </Labeled>
                            <Labeled>
                                <NumberField source="security_gate_threshold_high" />
                            </Labeled>
                            <Labeled>
                                <NumberField source="security_gate_threshold_medium" />
                            </Labeled>
                            <Labeled>
                                <NumberField source="security_gate_threshold_low" />
                            </Labeled>
                            <Labeled>
                                <NumberField source="security_gate_threshold_none" />
                            </Labeled>
                            <Labeled>
                                <NumberField source="security_gate_threshold_unknown" />
                            </Labeled>
                        </Stack>
                    )}
                </Fragment>
            )}

            {product.product_group && product.product_group_security_gate_active != null && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Security Gate
                    </Typography>
                    <Labeled label="Security gate (from product group)">
                        <BooleanField
                            source="product_group_security_gate_active"
                            valueLabelFalse="Disabled"
                            valueLabelTrue="Product group specific"
                        />
                    </Labeled>
                </Fragment>
            )}

            {product.issue_tracker_active && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Issue Tracker
                    </Typography>
                    <Labeled label="Active">
                        <BooleanField source="issue_tracker_active" />
                    </Labeled>
                    <Stack spacing={1}>
                        <Labeled>
                            <TextField source="issue_tracker_type" label="Type" />
                        </Labeled>
                        <Labeled>
                            <TextField source="issue_tracker_base_url" label="Base URL" />
                        </Labeled>
                        <Labeled>
                            <TextField source="issue_tracker_project_id" label="Project id" />
                        </Labeled>
                        {product.issue_tracker_labels && (
                            <Labeled>
                                <TextField source="issue_tracker_labels" label="Labels" />
                            </Labeled>
                        )}
                        {product.issue_tracker_minimum_severity && (
                            <Labeled>
                                <SeverityField source="issue_tracker_minimum_severity" label="Minimum severity" />
                            </Labeled>
                        )}
                        {product.issue_tracker_username && (
                            <Labeled>
                                <TextField source="issue_tracker_username" label="Username (only for Jira)" />
                            </Labeled>
                        )}
                        {product.issue_tracker_issue_type && (
                            <Labeled>
                                <TextField source="issue_tracker_issue_type" label="Issue type (only for Jira)" />
                            </Labeled>
                        )}
                        {product.issue_tracker_status_closed && (
                            <Labeled>
                                <TextField source="issue_tracker_status_closed" label="Closed status (only for Jira)" />
                            </Labeled>
                        )}
                    </Stack>
                </Fragment>
            )}

            {(product.assessments_need_approval ||
                product.product_group_assessments_need_approval ||
                product.product_rules_need_approval ||
                product.product_group_product_rules_need_approval ||
                product.new_observations_in_review ||
                product.product_group_new_observations_in_review) && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Review
                    </Typography>
                    <Stack spacing={1}>
                        <Labeled label="Assessments need approval">
                            <BooleanField source="assessments_need_approval" />
                        </Labeled>
                        {product.product_group_assessments_need_approval && (
                            <Labeled label="Assessments need approval (from product group)">
                                <BooleanField source="product_group_assessments_need_approval" />
                            </Labeled>
                        )}
                        <Labeled label="Rules need approval">
                            <BooleanField source="product_rules_need_approval" />
                        </Labeled>
                        {product.product_group_product_rules_need_approval && (
                            <Labeled label="Rules need approval (from product group)">
                                <BooleanField source="product_group_product_rules_need_approval" />
                            </Labeled>
                        )}
                        <Labeled label='Status "In review" for new observations'>
                            <BooleanField source="new_observations_in_review" />
                        </Labeled>
                        {product.product_group_new_observations_in_review && (
                            <Labeled label='Status "In review" for new observations (from product group)'>
                                <BooleanField source="product_group_new_observations_in_review" />
                            </Labeled>
                        )}
                    </Stack>
                </Fragment>
            )}

            {product.risk_acceptance_expiry_active != null && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Risk acceptance expiry
                    </Typography>

                    <Stack direction="row" spacing={4}>
                        <Labeled label="Risk acceptance expiry">
                            <BooleanField
                                source="risk_acceptance_expiry_active"
                                valueLabelFalse="Disabled"
                                valueLabelTrue="Product specific"
                            />
                        </Labeled>
                        {product.risk_acceptance_expiry_active && (
                            <Labeled label="Risk acceptance expiry (days)">
                                <NumberField source="risk_acceptance_expiry_days" />
                            </Labeled>
                        )}
                    </Stack>
                </Fragment>
            )}
            {product.license_policy && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        License management
                    </Typography>
                    <Labeled label="License policy">
                        <ReferenceField
                            source="license_policy"
                            reference="license_policies"
                            link="show"
                            sx={{ "& a": { textDecoration: "none" } }}
                        >
                            <TextField source="name" />
                        </ReferenceField>
                    </Labeled>
                </Fragment>
            )}

            {product.osv_enabled && (
                <Fragment>
                    <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Vulnerability scanning
                    </Typography>
                    <Stack direction="row" spacing={4}>
                        <Labeled label="OSV scanning enabled">
                            <BooleanField source="osv_enabled" sx={{ marginBottom: 2 }} />
                        </Labeled>
                        {product.osv_linux_distribution && (
                            <Labeled label="OSV Linux distribution">
                                <WithRecord
                                    render={(record) => (
                                        <OSVLinuxDistributionField
                                            osv_linux_distribution={record.osv_linux_distribution}
                                            osv_linux_release={record.osv_linux_release}
                                            label="OSV Linux distribution"
                                        />
                                    )}
                                />
                            </Labeled>
                        )}
                    </Stack>
                    {product.automatic_osv_scanning_enabled && (
                        <Labeled>
                            <BooleanField
                                source="automatic_osv_scanning_enabled"
                                label="Automatic OSV scanning enabled"
                            />
                        </Labeled>
                    )}
                </Fragment>
            )}
        </Fragment>
    );
};

export default ProductShowProduct;
