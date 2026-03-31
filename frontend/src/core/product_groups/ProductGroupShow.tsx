import BarChartIcon from "@mui/icons-material/BarChart";
import ChecklistIcon from "@mui/icons-material/Checklist";
import PeopleAltIcon from "@mui/icons-material/PeopleAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import TokenIcon from "@mui/icons-material/Token";
import { Badge, Divider, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    EditButton,
    Labeled,
    NumberField,
    PrevNextButtons,
    ReferenceField,
    Show,
    Tab,
    TabbedShowLayout,
    TabbedShowLayoutTabs,
    TextArrayField,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import ApiTokenCreate from "../../access_control/api_tokens/ApiTokenCreate";
import ApiTokenEmbeddedList from "../../access_control/api_tokens/ApiTokenEmbeddedList";
import {
    PERMISSION_PRODUCT_API_TOKEN_CREATE,
    PERMISSION_PRODUCT_AUTHORIZATION_GROUP_MEMBER_CREATE,
    PERMISSION_PRODUCT_GROUP_EDIT,
    PERMISSION_PRODUCT_MEMBER_CREATE,
    PERMISSION_PRODUCT_RULE_APPLY,
    PERMISSION_PRODUCT_RULE_CREATE,
} from "../../access_control/types";
import MarkdownField from "../../commons/custom_fields/MarkdownField";
import { feature_email } from "../../commons/functions";
import MetricsHeader from "../../metrics/MetricsHeader";
import MetricsSeveritiesCurrent from "../../metrics/MetricsSeveritiesCurrent";
import MetricsSeveritiesTimeline from "../../metrics/MetricsSeveritiesTimeLine";
import MetricsStatusCurrent from "../../metrics/MetricsStatusCurrent";
import general_rules from "../../rules/general_rules";
import ProductRuleApply from "../../rules/product_rules/ProductRuleApply";
import ProductRuleCreate from "../../rules/product_rules/ProductRuleCreate";
import ProductRuleEmbeddedList from "../../rules/product_rules/ProductRuleEmbeddedList";
import ProductAuthorizationGroupMemberAdd from "../product_authorization_group_members/ProductAuthorizationGroupMemberAdd";
import ProductAuthorizationGroupMemberEmbeddedList from "../product_authorization_group_members/ProductAuthorizationGroupMemberEmbeddedList";
import ProductMemberAdd from "../product_members/ProductMemberAdd";
import ProductMemberEmbeddedList from "../product_members/ProductMemberEmbeddedList";
import product from "../products";
import ExportMenu from "../products/ExportMenu";
import ProductCreateDialog from "../products/ProductCreateDialog";
import ProductEmbeddedList from "../products/ProductEmbeddedList";
import ProductGroupHeader from "./ProductGroupHeader";
import ProductGroupReviews from "./ProductGroupReviews";

const ShowActions = () => {
    const product_group = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "name", order: "ASC" }}
                    storeKey="product_groups.list"
                    queryOptions={{ meta: { api_resource: "product_group_names" } }}
                />
                <ExportMenu product={product_group} is_product_group={true} />
                {product_group?.permissions.includes(PERMISSION_PRODUCT_GROUP_EDIT) && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const ProductGroupShow = () => {
    return (
        <Fragment>
            <ProductGroupHeader />
            <Show actions={<ShowActions />}>
                <WithRecord
                    render={(product_group) => (
                        <TabbedShowLayout tabs={<TabbedShowLayoutTabs variant="scrollable" scrollButtons="auto" />}>
                            <Tab label="Products" icon={<product.icon />}>
                                <ProductCreateDialog productGroupId={product_group.id} />
                                <ProductEmbeddedList product_group={product_group} />
                            </Tab>
                            <Tab label="Metrics" path="metrics" icon={<BarChartIcon />}>
                                <MetricsHeader repository_default_branch={undefined} />
                                <Stack
                                    direction="row"
                                    spacing={2}
                                    sx={{
                                        alignItems: "center",
                                        marginTop: 1,
                                        marginBottom: 1,
                                    }}
                                >
                                    <MetricsSeveritiesCurrent product_id={product_group.id} />
                                    <MetricsSeveritiesTimeline product_id={product_group.id} />
                                    <MetricsStatusCurrent product_id={product_group.id} />
                                </Stack>
                            </Tab>
                            {product_group.product_rule_approvals > 0 && (
                                <Tab
                                    label="Reviews"
                                    path="reviews"
                                    icon={
                                        <Badge badgeContent={product_group.product_rule_approvals} color="secondary">
                                            <ChecklistIcon />
                                        </Badge>
                                    }
                                >
                                    <ProductGroupReviews product_group={product_group} />
                                </Tab>
                            )}
                            <Tab label="Settings" icon={<SettingsIcon />} path="settings">
                                <Typography variant="h6">Settings</Typography>
                                <Stack spacing={1}>
                                    <Labeled>
                                        <TextField source="name" />
                                    </Labeled>
                                    {product_group.description && (
                                        <Labeled>
                                            <MarkdownField content={product_group.description} label="Description" />
                                        </Labeled>
                                    )}
                                </Stack>
                                {product_group.repository_branch_housekeeping_active != null && (
                                    <Fragment>
                                        <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                            Housekeeping
                                        </Typography>

                                        <Stack direction="row" spacing={4} sx={{ marginTop: 1 }}>
                                            <Labeled label="Housekeeping">
                                                <BooleanField
                                                    source="repository_branch_housekeeping_active"
                                                    valueLabelFalse="Disabled"
                                                    valueLabelTrue="Product group specific"
                                                />
                                            </Labeled>
                                            {product_group.repository_branch_housekeeping_active &&
                                                product_group.repository_branch_housekeeping_keep_inactive_days && (
                                                    <Labeled label="Keep inactive">
                                                        <NumberField source="repository_branch_housekeeping_keep_inactive_days" />
                                                    </Labeled>
                                                )}
                                            {product_group.repository_branch_housekeeping_active &&
                                                product_group.repository_branch_housekeeping_exempt_branches && (
                                                    <Labeled label="Exempt branches / versions">
                                                        <TextField source="repository_branch_housekeeping_exempt_branches" />
                                                    </Labeled>
                                                )}
                                        </Stack>
                                    </Fragment>
                                )}
                                {((feature_email() && product_group.notification_email_to) ||
                                    product_group.notification_ms_teams_webhook ||
                                    product_group.notification_slack_webhook ||
                                    product_group.observation_notification_min_severity ||
                                    (product_group.observation_notification_status_list &&
                                        product_group.observation_notification_status_list.length > 0) ||
                                    product_group.observation_notification_min_priority) && (
                                    <Fragment>
                                        <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                            Notifications
                                        </Typography>
                                        <Stack spacing={1}>
                                            {feature_email() && product_group.notification_email_to && (
                                                <Labeled label="Email">
                                                    <TextField source="notification_email_to" />
                                                </Labeled>
                                            )}
                                            {product_group.notification_ms_teams_webhook && (
                                                <Labeled label="MS Teams">
                                                    <TextField source="notification_ms_teams_webhook" />
                                                </Labeled>
                                            )}
                                            {product_group.notification_slack_webhook && (
                                                <Labeled label="Slack">
                                                    <TextField source="notification_slack_webhook" />
                                                </Labeled>
                                            )}
                                            {product_group.observation_notification_min_severity && (
                                                <Labeled label="Minimum severity for observation notifications">
                                                    <TextField source="observation_notification_min_severity" />
                                                </Labeled>
                                            )}
                                            {product_group.observation_notification_status_list &&
                                                product_group.observation_notification_status_list.length > 0 && (
                                                    <Labeled label="Statuses for observation notifications">
                                                        <TextArrayField source="observation_notification_status_list" />
                                                    </Labeled>
                                                )}
                                            {product_group.observation_notification_min_priority && (
                                                <Labeled label="Minimum priority for observation notifications">
                                                    <TextField source="observation_notification_min_priority" />
                                                </Labeled>
                                            )}
                                        </Stack>
                                    </Fragment>
                                )}
                                {product_group.security_gate_active != null && (
                                    <Fragment>
                                        <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                            Security Gate
                                        </Typography>
                                        <Labeled label="Security gate">
                                            <BooleanField
                                                source="security_gate_active"
                                                valueLabelFalse="Disabled"
                                                valueLabelTrue="Product group specific"
                                            />
                                        </Labeled>
                                        {product_group.security_gate_active && (
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

                                {(product_group.assessments_need_approval ||
                                    product_group.product_rules_need_approval ||
                                    product_group.new_observations_in_review) && (
                                    <Fragment>
                                        <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                            Review
                                        </Typography>
                                        <Stack spacing={1}>
                                            {product_group.assessments_need_approval && (
                                                <Labeled label="Assessments need approval">
                                                    <BooleanField source="assessments_need_approval" />
                                                </Labeled>
                                            )}
                                            {product_group.product_rules_need_approval && (
                                                <Labeled label="Rules need approval">
                                                    <BooleanField source="product_rules_need_approval" />
                                                </Labeled>
                                            )}
                                            {product_group.new_observations_in_review && (
                                                <Labeled label='Status "In review" for new observations'>
                                                    <BooleanField source="new_observations_in_review" />
                                                </Labeled>
                                            )}
                                        </Stack>
                                    </Fragment>
                                )}

                                {product_group.risk_acceptance_expiry_active != null && (
                                    <Fragment>
                                        <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                            Risk acceptance expiry
                                        </Typography>

                                        <Labeled label="Risk acceptance expiry">
                                            <BooleanField
                                                source="risk_acceptance_expiry_active"
                                                valueLabelFalse="Disabled"
                                                valueLabelTrue="Product group specific"
                                            />
                                        </Labeled>
                                        {product_group.risk_acceptance_expiry_active && (
                                            <Stack spacing={1}>
                                                <Labeled label="Risk acceptance expiry (days)">
                                                    <NumberField source="risk_acceptance_expiry_days" />
                                                </Labeled>
                                            </Stack>
                                        )}
                                    </Fragment>
                                )}

                                {product_group.license_policy && (
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
                            </Tab>
                            <Tab label="Rules" path="rules" icon={<general_rules.icon />}>
                                <Stack
                                    direction="row"
                                    spacing={2}
                                    sx={{
                                        alignItems: "center",
                                    }}
                                >
                                    {product_group?.permissions.includes(PERMISSION_PRODUCT_RULE_CREATE) && (
                                        <ProductRuleCreate product={product_group} />
                                    )}
                                    {product_group?.permissions.includes(PERMISSION_PRODUCT_RULE_APPLY) && (
                                        <ProductRuleApply product={product_group} />
                                    )}
                                </Stack>
                                <ProductRuleEmbeddedList product={product_group} />
                            </Tab>
                            <Tab label="Members" path="members" icon={<PeopleAltIcon />}>
                                <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                    User members
                                </Typography>
                                {product_group?.permissions.includes(PERMISSION_PRODUCT_MEMBER_CREATE) && (
                                    <ProductMemberAdd id={product_group.id} />
                                )}
                                <ProductMemberEmbeddedList product={product_group} />

                                <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                    Authorization group members
                                </Typography>
                                {product_group?.permissions.includes(
                                    PERMISSION_PRODUCT_AUTHORIZATION_GROUP_MEMBER_CREATE
                                ) && <ProductAuthorizationGroupMemberAdd id={product_group.id} />}
                                <ProductAuthorizationGroupMemberEmbeddedList product={product_group} />
                            </Tab>
                            <Tab label="API Token" path="api_token" icon={<TokenIcon />}>
                                {product_group?.permissions.includes(PERMISSION_PRODUCT_API_TOKEN_CREATE) && (
                                    <ApiTokenCreate type="product" product={product_group} />
                                )}
                                <ApiTokenEmbeddedList type="product" product={product_group} />
                            </Tab>
                        </TabbedShowLayout>
                    )}
                />
            </Show>
        </Fragment>
    );
};

export default ProductGroupShow;
