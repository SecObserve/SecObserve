import { Stack } from "@mui/material";
import { Fragment } from "react";
import { EditButton, PrevNextButtons, Show, TopToolbar, WithRecord, useRecordContext } from "react-admin";

import { feature_general_rules_need_approval_enabled, is_superuser } from "../../commons/functions";
import RuleApproval from "../RuleApproval";
import RuleSimulation from "../RuleSimulation";
import { RuleShowComponent } from "../functions";
import { RULE_STATUS_NEEDS_APPROVAL } from "../types";

const ShowActions = () => {
    const rule = useRecordContext();
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <PrevNextButtons linkType="show" sort={{ field: "name", order: "ASC" }} storeKey="general_rules.list" />
                {rule?.approval_status == RULE_STATUS_NEEDS_APPROVAL &&
                    feature_general_rules_need_approval_enabled() &&
                    is_superuser() && <RuleApproval rule_id={rule.id} class="general_rules" />}
                {rule && <RuleSimulation rule={rule} />}
                {is_superuser() && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const GeneralRuleComponent = () => {
    return <WithRecord render={(rule) => <RuleShowComponent rule={rule} />} />;
};

const GeneralRuleShow = () => {
    return (
        <Show actions={<ShowActions />} component={GeneralRuleComponent}>
            <Fragment />
        </Show>
    );
};

export default GeneralRuleShow;
