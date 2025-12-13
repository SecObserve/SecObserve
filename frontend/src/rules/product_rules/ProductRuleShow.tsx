import { Stack } from "@mui/material";
import { Fragment } from "react";
import { EditButton, PrevNextButtons, Show, SortPayload, TopToolbar, WithRecord, useRecordContext } from "react-admin";

import { PERMISSION_PRODUCT_RULE_APPROVAL, PERMISSION_PRODUCT_RULE_EDIT } from "../../access_control/types";
import { ASSESSMENT_STATUS_NEEDS_APPROVAL } from "../../core/types";
import RuleApproval from "../RuleApproval";
import RuleSimulation from "../RuleSimulation";
import { RuleShowComponent } from "../functions";
import { RULE_STATUS_NEEDS_APPROVAL } from "../types";

const ShowActions = () => {
    const rule = useRecordContext();

    let filter = null;
    const sort: SortPayload = { field: "name", order: "ASC" };
    let storeKey = null;
    if (rule && localStorage.getItem("productruleembeddedlist")) {
        filter = { product: Number(rule.product_data.id) };
        storeKey = "product_rules.embedded";
    }
    if (rule && localStorage.getItem("productruleapprovallist")) {
        filter = {
            product: Number(rule.product_data.id),
            approval_status: ASSESSMENT_STATUS_NEEDS_APPROVAL,
        };
        storeKey = "product_rules.approval";
    }

    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                {rule && filter && sort && storeKey && (
                    <PrevNextButtons filter={filter} linkType="show" sort={sort} storeKey={storeKey} />
                )}
                {rule?.approval_status == RULE_STATUS_NEEDS_APPROVAL &&
                    (rule?.product_data.product_rules_need_approval ||
                        rule?.product_data.product_group_product_rules_need_approval) &&
                    rule?.product_data.permissions.includes(PERMISSION_PRODUCT_RULE_APPROVAL) && (
                        <RuleApproval rule_id={rule.id} class="product_rules" />
                    )}
                {rule && <RuleSimulation rule_id={rule.id} rules_provider="product_rules" />}
                {rule?.product_data.permissions.includes(PERMISSION_PRODUCT_RULE_EDIT) && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const ProductRuleComponent = () => {
    return <WithRecord render={(rule) => <RuleShowComponent rule={rule} />} />;
};

const GeneralRuleShow = () => {
    return (
        <Show actions={<ShowActions />} component={ProductRuleComponent}>
            <Fragment />
        </Show>
    );
};

export default GeneralRuleShow;
