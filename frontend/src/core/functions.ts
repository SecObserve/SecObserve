export const transform_product_group_and_product = (data: any, description: string) => {
    data.description = description;

    if (data.repository_branch_housekeeping_active) {
        data.repository_branch_housekeeping_keep_inactive_days ||= 1;
    } else {
        data.repository_branch_housekeeping_keep_inactive_days ||= null;
    }
    data.repository_branch_housekeeping_exempt_branches ??= "";

    data.notification_email_to ??= "";
    data.notification_ms_teams_webhook ??= "";
    data.notification_slack_webhook ??= "";

    if (data.security_gate_active) {
        data.security_gate_threshold_critical ||= 0;
        data.security_gate_threshold_high ||= 0;
        data.security_gate_threshold_medium ||= 0;
        data.security_gate_threshold_low ||= 0;
        data.security_gate_threshold_none ||= 0;
        data.security_gate_threshold_unknown ||= 0;
    } else {
        data.security_gate_threshold_critical ||= null;
        data.security_gate_threshold_high ||= null;
        data.security_gate_threshold_medium ||= null;
        data.security_gate_threshold_low ||= null;
        data.security_gate_threshold_none ||= null;
        data.security_gate_threshold_unknown ||= null;
    }

    if (data.risk_acceptance_expiry_active) {
        data.risk_acceptance_expiry_days ||= 30;
    } else {
        data.risk_acceptance_expiry_days ||= null;
    }

    data.observation_notification_min_severity ??= "";

    return data;
};
