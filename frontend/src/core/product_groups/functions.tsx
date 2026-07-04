import { Divider, Stack, Typography } from "@mui/material";
import { Fragment, useEffect } from "react";
import {
    AutocompleteArrayInput,
    BooleanInput,
    FormDataConsumer,
    Identifier,
    NullableBooleanInput,
    NumberInput,
    ReferenceArrayInput,
    ReferenceInput,
    useRecordContext,
} from "react-admin";
import { useFormContext } from "react-hook-form";

import product_groups from ".";
import { DesignatedApproversInput } from "../../commons/custom_fields/DesignatedApproversInput";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import { validate_0_999999, validate_255, validate_2048, validate_required_255 } from "../../commons/custom_validators";
import { feature_email, feature_license_management } from "../../commons/functions";
import {
    AutocompleteArrayInputWide,
    AutocompleteInputMedium,
    AutocompleteInputWide,
    TextInputExtraWide,
    TextInputWide,
} from "../../commons/layout/themes";
import { OBSERVATION_SEVERITY_CHOICES, OBSERVATION_STATUS_CHOICES } from "../types";

export type ProductGroupCreateEditComponentProps = {
    initialDescription: string;
    setDescription: (value: string) => void;
};

// Pre-fills the designated approvers with the current user when the field first appears (create form).
const DefaultApprover = ({ userId }: { userId: Identifier }) => {
    const { getValues, setValue } = useFormContext();
    useEffect(() => {
        if (!getValues("assessment_approvers")?.length) {
            setValue("assessment_approvers", [userId], { shouldDirty: true });
        }
    }, [getValues, setValue, userId]);
    return null;
};

export const ProductGroupCreateEditComponent = ({
    initialDescription,
    setDescription,
}: ProductGroupCreateEditComponentProps) => {
    const product_group = useRecordContext();
    // Limit approver choices to members with an approval-capable role on this product group.
    const approver_filter = { assessment_approver_for_product: product_group?.id ?? 0 };
    // On create, pre-fill the designated approvers with the current user (who becomes the Owner of the new
    // product group); on edit, keep the saved list so it can be refined once members have been added.
    const stored_user = localStorage.getItem("user");
    const current_user_id = stored_user ? JSON.parse(stored_user).id : undefined;
    const default_approver_on_create = product_group?.id ? undefined : current_user_id;
    return (
        <Fragment>
            <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                <product_groups.icon />
                &nbsp;&nbsp;Product Group
            </Typography>
            <TextInputWide autoFocus source="name" validate={validate_required_255} />
            <MarkdownEdit
                initialValue={initialDescription}
                setValue={setDescription}
                label="Description"
                maxLength={2048}
            />

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Housekeeping
            </Typography>
            <NullableBooleanInput
                source="repository_branch_housekeeping_active"
                label="Housekeeping"
                defaultValue={null}
                nullLabel="Standard"
                falseLabel="Disabled"
                trueLabel="Product group specific"
                helperText="Delete inactive branches / versions"
            />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.repository_branch_housekeeping_active && (
                        <Stack spacing={2}>
                            <NumberInput
                                source="repository_branch_housekeeping_keep_inactive_days"
                                label="Keep inactive"
                                helperText="Days before inactive branches / versions and their observations are deleted"
                                defaultValue={30}
                                min={1}
                                max={999999}
                                validate={validate_0_999999}
                            />
                            <TextInputWide
                                source="repository_branch_housekeeping_exempt_branches"
                                label="Exempt branches / versions"
                                helperText="Regular expression which branches / versions to exempt from deletion"
                                validate={validate_255}
                            />
                        </Stack>
                    )
                }
            </FormDataConsumer>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Notifications
            </Typography>
            <Stack spacing={1}>
                {feature_email() && (
                    <TextInputExtraWide
                        source="notification_email_to"
                        label="Comma separated email to addresses to send notifications via email"
                        validate={validate_255}
                    />
                )}
                <TextInputExtraWide
                    source="notification_ms_teams_webhook"
                    label="Webhook URL to send notifications to MS Teams"
                    validate={validate_2048}
                />
                <TextInputExtraWide
                    source="notification_slack_webhook"
                    label="Webhook URL to send notifications to Slack"
                    validate={validate_2048}
                />
                <AutocompleteInputMedium
                    source="observation_notification_min_severity"
                    label="Minimum severity for observation notifications"
                    choices={OBSERVATION_SEVERITY_CHOICES}
                    sx={{ width: "25em" }}
                />
                <AutocompleteArrayInput
                    source="observation_notification_status_list"
                    label="Statuses for observation notifications"
                    choices={OBSERVATION_STATUS_CHOICES}
                    sx={{ width: "25em" }}
                />
                <NumberInput
                    source="observation_notification_min_priority"
                    label="Minimum priority for observation notifications"
                    step={1}
                    min={1}
                    max={99}
                    sx={{ width: "25em" }}
                />
            </Stack>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Security Gate
            </Typography>
            <NullableBooleanInput
                source="security_gate_active"
                defaultValue={null}
                nullLabel="Standard"
                falseLabel="Disabled"
                trueLabel="Product group specific"
                label="Security gate"
                helperText="Shows that a product does not exceed a defined amount of vulnerabilities per severity"
            />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.security_gate_active && (
                        <Stack spacing={1}>
                            <NumberInput
                                label="Threshold critical"
                                source="security_gate_threshold_critical"
                                min={0}
                                max={999999}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold high"
                                source="security_gate_threshold_high"
                                min={0}
                                max={999999}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold medium"
                                source="security_gate_threshold_medium"
                                min={0}
                                max={999999}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold low"
                                source="security_gate_threshold_low"
                                min={0}
                                max={999999}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold none"
                                source="security_gate_threshold_none"
                                min={0}
                                max={999999}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold unknown"
                                source="security_gate_threshold_unknown"
                                min={0}
                                max={999999}
                                validate={validate_0_999999}
                            />
                        </Stack>
                    )
                }
            </FormDataConsumer>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Review
            </Typography>
            <BooleanInput source="assessments_need_approval" label="Assessments need approval" defaultValue={false} />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.assessments_need_approval && (
                        <Fragment>
                            <DesignatedApproversInput
                                approver_filter={approver_filter}
                                helperText="Users allowed to approve assessments for all products in this group. Empty for default permission."
                            />
                            <ReferenceArrayInput
                                source="assessment_approver_authorization_groups"
                                reference="authorization_groups"
                                filter={approver_filter}
                                sort={{ field: "name", order: "ASC" }}
                            >
                                <AutocompleteArrayInputWide
                                    label="Designated approver groups"
                                    optionText="name"
                                    helperText="Groups whose members may approve assessments for all products in this group."
                                />
                            </ReferenceArrayInput>
                            {default_approver_on_create && <DefaultApprover userId={default_approver_on_create} />}
                        </Fragment>
                    )
                }
            </FormDataConsumer>
            <BooleanInput source="product_rules_need_approval" label="Rules need approval" defaultValue={false} />
            <BooleanInput
                source="new_observations_in_review"
                label='Status "In review" for new observations'
                defaultValue={false}
            />

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Risk acceptance expiry
            </Typography>
            <NullableBooleanInput
                source="risk_acceptance_expiry_active"
                label="Risk acceptance expiry"
                defaultValue={null}
                nullLabel="Standard"
                falseLabel="Disabled"
                trueLabel="Product group specific"
                helperText="Set date for expiry or risk acceptance"
                sx={{ width: "15em", marginBottom: 2 }}
            />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.risk_acceptance_expiry_active && (
                        <Stack spacing={2}>
                            <NumberInput
                                source="risk_acceptance_expiry_days"
                                label="Risk acceptance expiry (days)"
                                helperText="Days after which the risk acceptance expires"
                                defaultValue={30}
                                min={1}
                                max={999999}
                                validate={validate_0_999999}
                            />
                        </Stack>
                    )
                }
            </FormDataConsumer>

            {feature_license_management() && (
                <Fragment>
                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        License management
                    </Typography>
                    <ReferenceInput
                        source="license_policy"
                        reference="license_policies"
                        label="License policy"
                        sort={{ field: "name", order: "ASC" }}
                    >
                        <AutocompleteInputWide optionText="name" />
                    </ReferenceInput>
                </Fragment>
            )}
        </Fragment>
    );
};
