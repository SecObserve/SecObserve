import BarChartIcon from "@mui/icons-material/BarChart";
import ChecklistIcon from "@mui/icons-material/Checklist";
import PeopleAltIcon from "@mui/icons-material/PeopleAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import TokenIcon from "@mui/icons-material/Token";
import { Badge, Divider, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    EditButton,
    PrevNextButtons,
    Show,
    Tab,
    TabbedShowLayout,
    TabbedShowLayoutTabs,
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
import MetricsHeader from "../../metrics/MetricsHeader";
import MetricsSeveritiesCurrent from "../../metrics/MetricsSeveritiesCurrent";
import MetricsSeveritiesTimeline from "../../metrics/MetricsSeveritiesTimeLine";
import MetricsStatusCurrent from "../../metrics/MetricsStatusCurrent";
import notifications from "../../notifications/notifications";
import ProductNotificationSettings from "../../notifications/product_notifications/ProductNotificationSettings";
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
import { ProductGroup } from "../types";
import ProductGroupHeader from "./ProductGroupHeader";
import ProductGroupReviews from "./ProductGroupReviews";
import ProductGroupShowProductGroup from "./ProductGroupShowProductGroup";

const ShowActions = () => {
    const product_group = useRecordContext<ProductGroup>();
    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "name", order: "ASC" }}
                    storeKey="product_groups.list"
                    queryOptions={{ meta: { api_resource: "product_group_names" } }}
                />
                <ExportMenu product={product_group} is_product_group={true} />
                {product_group?.permissions?.includes(PERMISSION_PRODUCT_GROUP_EDIT) && <EditButton />}
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
                            {product_group.product_rule_approvals + product_group.observation_log_approvals > 0 && (
                                <Tab
                                    label="Reviews"
                                    path="reviews"
                                    icon={
                                        <Badge
                                            badgeContent={
                                                product_group.product_rule_approvals +
                                                product_group.observation_log_approvals
                                            }
                                            color="secondary"
                                        >
                                            <ChecklistIcon />
                                        </Badge>
                                    }
                                >
                                    <ProductGroupReviews product_group={product_group} />
                                </Tab>
                            )}
                            <Tab label="Settings" icon={<SettingsIcon />} path="settings">
                                {/* Keyed, so that the sections start closed again for the next product group. */}
                                <ProductGroupShowProductGroup key={product_group.id} product_group={product_group} />
                            </Tab>
                            <Tab label="Rules" path="rules" icon={<general_rules.icon />}>
                                <Stack
                                    direction="row"
                                    spacing={2}
                                    sx={{
                                        alignItems: "center",
                                    }}
                                >
                                    {product_group?.permissions?.includes(PERMISSION_PRODUCT_RULE_CREATE) && (
                                        <ProductRuleCreate product={product_group} />
                                    )}
                                    {product_group?.permissions?.includes(PERMISSION_PRODUCT_RULE_APPLY) && (
                                        <ProductRuleApply product={product_group} />
                                    )}
                                </Stack>
                                <ProductRuleEmbeddedList product={product_group} />
                            </Tab>
                            <Tab label="Members" path="members" icon={<PeopleAltIcon />}>
                                <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                    User members
                                </Typography>
                                {product_group?.permissions?.includes(PERMISSION_PRODUCT_MEMBER_CREATE) && (
                                    <ProductMemberAdd id={product_group.id} />
                                )}
                                <ProductMemberEmbeddedList product={product_group} />

                                <Divider sx={{ marginTop: 2, marginBottom: 2 }} />
                                <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                    Authorization group members
                                </Typography>
                                {product_group?.permissions?.includes(
                                    PERMISSION_PRODUCT_AUTHORIZATION_GROUP_MEMBER_CREATE
                                ) && <ProductAuthorizationGroupMemberAdd id={product_group.id} />}
                                <ProductAuthorizationGroupMemberEmbeddedList product={product_group} />
                            </Tab>
                            <Tab label="API Token" path="api_token" icon={<TokenIcon />}>
                                {product_group?.permissions?.includes(PERMISSION_PRODUCT_API_TOKEN_CREATE) && (
                                    <ApiTokenCreate type="product" product={product_group} />
                                )}
                                <ApiTokenEmbeddedList type="product" product={product_group} />
                            </Tab>
                            <Tab label="Notifications" path="notifications" icon={<notifications.icon />}>
                                <ProductNotificationSettings product={product_group} is_product_group={true} />
                            </Tab>
                        </TabbedShowLayout>
                    )}
                />
            </Show>
        </Fragment>
    );
};

export default ProductGroupShow;
