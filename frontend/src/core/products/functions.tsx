import { Divider, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanInput,
    FormDataConsumer,
    Identifier,
    NullableBooleanInput,
    NumberInput,
    ReferenceInput,
} from "react-admin";

import products from ".";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import OSVLinuxDistributionInput from "../../commons/custom_fields/OSVLinuxDistributionInput";
import { validate_0_999999, validate_255, validate_required_255 } from "../../commons/custom_validators";
import { feature_automatic_osv_scanning, feature_email, feature_license_management } from "../../commons/functions";
import { AutocompleteInputMedium, AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";
import { transform_product_group_and_product } from "../functions";
import { ISSUE_TRACKER_TYPE_CHOICES, OBSERVATION_SEVERITY_CHOICES } from "../types";

export const transform = (data: any, description: string) => {
    data = transform_product_group_and_product(data, description);

    data.purl ??= "";
    data.cpe23 ??= "";
    data.repository_prefix ??= "";

    data.issue_tracker_type ??= "";
    data.issue_tracker_base_url ??= "";
    data.issue_tracker_api_key ??= "";
    data.issue_tracker_project_id ??= "";
    data.issue_tracker_labels ??= "";
    data.issue_tracker_username ??= "";
    data.issue_tracker_issue_type ??= "";
    data.issue_tracker_status_closed ??= "";
    data.issue_tracker_minimum_severity ??= "";

    if (!data.osv_enabled) {
        data.osv_linux_distribution = "";
        data.osv_linux_release = "";
        data.automatic_osv_scanning_enabled = false;
    }
    data.osv_linux_distribution ??= "";
    data.osv_linux_release ??= "";

    return data;
};

export type ProductCreateEditComponentProps = {
    initialDescription: string;
    setDescription: (value: string) => void;
    productGroupId?: Identifier;
};

export const ProductCreateEditComponent = ({
    initialDescription,
    setDescription,
    productGroupId,
}: ProductCreateEditComponentProps) => {
    return (
        <Fragment>
            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                <products.icon />
                &nbsp;&nbsp;Product
            </Typography>
            <TextInputWide autoFocus source="name" validate={validate_required_255} />
            <MarkdownEdit
                initialValue={initialDescription}
                setValue={setDescription}
                label="Description"
                maxLength={2048}
            />
            {!productGroupId && (
                <ReferenceInput
                    source="product_group"
                    reference="product_groups"
                    queryOptions={{ meta: { api_resource: "product_group_names" } }}
                    sort={{ field: "name", order: "ASC" }}
                >
                    <AutocompleteInputWide optionText="name" />
                </ReferenceInput>
            )}
            {productGroupId && (
                <ReferenceInput
                    source="product_group"
                    reference="product_groups"
                    queryOptions={{ meta: { api_resource: "product_group_names" } }}
                    sort={{ field: "name", order: "ASC" }}
                >
                    <AutocompleteInputWide optionText="name" defaultValue={productGroupId} disabled={true} />
                </ReferenceInput>
            )}
            <Stack direction="row" spacing={4}>
                <TextInputWide source="purl" validate={validate_255} label="PURL" />
                <TextInputWide source="cpe23" validate={validate_255} label="CPE 2.3" />
            </Stack>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Rules
            </Typography>
            <BooleanInput source="apply_general_rules" defaultValue={true} />

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Source code repository and housekeeping
            </Typography>
            <TextInputWide
                source="repository_prefix"
                helperText="URL prefix to link to a file in the source code repository"
                validate={validate_255}
                sx={{ marginBottom: 3 }}
            />
            <Stack direction="row" spacing={4}>
                <NullableBooleanInput
                    source="repository_branch_housekeeping_active"
                    label="Housekeeping"
                    defaultValue={null}
                    nullLabel="Standard"
                    falseLabel="Disabled"
                    trueLabel="Product specific"
                    helperText="Delete inactive branches / versions"
                    sx={{ marginBottom: 2 }}
                />
                <FormDataConsumer>
                    {({ formData }) =>
                        formData.repository_branch_housekeeping_active && (
                            <Fragment>
                                <NumberInput
                                    source="repository_branch_housekeeping_keep_inactive_days"
                                    label="Keep inactive"
                                    helperText="Days before inactive branches / versions and their observations are deleted"
                                    defaultValue={30}
                                    min={1}
                                    max={999999}
                                    sx={{ width: "10em" }}
                                    validate={validate_0_999999}
                                />
                                <TextInputWide
                                    source="repository_branch_housekeeping_exempt_branches"
                                    label="Exempt branches / versions"
                                    helperText="Regular expression which branches / version to exempt from deletion"
                                    validate={validate_255}
                                />
                            </Fragment>
                        )
                    }
                </FormDataConsumer>
            </Stack>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Notifications
            </Typography>
            <Stack spacing={2}>
                {feature_email() && (
                    <TextInputWide
                        source="notification_email_to"
                        label="Email"
                        helperText="Comma separated email to addresses"
                        validate={validate_255}
                    />
                )}
                <TextInputWide
                    source="notification_ms_teams_webhook"
                    label="MS Teams"
                    helperText="Webhook URL to send notifications to MS Teams"
                    validate={validate_255}
                />
                <TextInputWide
                    source="notification_slack_webhook"
                    label="Slack"
                    helperText="Webhook URL to send notifications to Slack"
                    validate={validate_255}
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
                trueLabel="Product specific"
                label="Security gate"
                helperText="Shows that the product does not exceed a defined amount of vulnerabilities per severity"
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
                                sx={{ width: "12em" }}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold high"
                                source="security_gate_threshold_high"
                                min={0}
                                max={999999}
                                sx={{ width: "12em" }}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold medium"
                                source="security_gate_threshold_medium"
                                min={0}
                                max={999999}
                                sx={{ width: "12em" }}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold low"
                                source="security_gate_threshold_low"
                                min={0}
                                max={999999}
                                sx={{ width: "12em" }}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold none"
                                source="security_gate_threshold_none"
                                min={0}
                                max={999999}
                                sx={{ width: "12em" }}
                                validate={validate_0_999999}
                            />
                            <NumberInput
                                label="Threshold unknown"
                                source="security_gate_threshold_unknown"
                                min={0}
                                max={999999}
                                sx={{ width: "12em" }}
                                validate={validate_0_999999}
                            />
                        </Stack>
                    )
                }
            </FormDataConsumer>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Issue Tracker
            </Typography>
            <BooleanInput
                source="issue_tracker_active"
                label="Active"
                defaultValue={false}
                helperText="Send observations to an issue tracker"
                sx={{ marginBottom: 2 }}
            />
            <AutocompleteInputMedium source="issue_tracker_type" label="Type" choices={ISSUE_TRACKER_TYPE_CHOICES} />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.issue_tracker_type && (
                        <Stack spacing={1}>
                            <TextInputWide source="issue_tracker_base_url" label="Base URL" validate={validate_255} />
                            <TextInputWide source="issue_tracker_api_key" label="API key" validate={validate_255} />
                            <TextInputWide
                                source="issue_tracker_project_id"
                                label="Project id"
                                validate={validate_255}
                            />
                            <TextInputWide source="issue_tracker_labels" label="Labels" validate={validate_255} />
                            <AutocompleteInputMedium
                                source="issue_tracker_minimum_severity"
                                label="Minimum severity"
                                choices={OBSERVATION_SEVERITY_CHOICES}
                            />
                            <FormDataConsumer>
                                {({ formData }) =>
                                    formData.issue_tracker_type == "Jira" && (
                                        <Stack spacing={1}>
                                            <TextInputWide
                                                source="issue_tracker_username"
                                                label="Username (only for Jira)"
                                                validate={validate_255}
                                            />
                                            <TextInputWide
                                                source="issue_tracker_issue_type"
                                                label="Issue type (only for Jira)"
                                                validate={validate_255}
                                            />
                                            <TextInputWide
                                                source="issue_tracker_status_closed"
                                                label="Closed status (only for Jira)"
                                                validate={validate_255}
                                            />
                                        </Stack>
                                    )
                                }
                            </FormDataConsumer>
                        </Stack>
                    )
                }
            </FormDataConsumer>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Review
            </Typography>
            <BooleanInput source="assessments_need_approval" label="Assessments need approval" defaultValue={false} />
            <BooleanInput source="product_rules_need_approval" label="Rules need approval" defaultValue={false} />
            <BooleanInput
                source="new_observations_in_review"
                label='Status "In review" for new observations'
                defaultValue={false}
            />

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Risk acceptance expiry
            </Typography>
            <Stack direction="row" spacing={4}>
                <NullableBooleanInput
                    source="risk_acceptance_expiry_active"
                    label="Risk acceptance expiry"
                    defaultValue={null}
                    nullLabel="Standard"
                    falseLabel="Disabled"
                    trueLabel="Product specific"
                    helperText="Set date for expiry or risk acceptance"
                    sx={{ width: "15em", marginBottom: 2 }}
                />
                <FormDataConsumer>
                    {({ formData }) =>
                        formData.risk_acceptance_expiry_active && (
                            <NumberInput
                                source="risk_acceptance_expiry_days"
                                label="Risk acceptance expiry (days)"
                                helperText="Days after which the risk acceptance expires"
                                defaultValue={30}
                                min={1}
                                max={999999}
                                validate={validate_0_999999}
                            />
                        )
                    }
                </FormDataConsumer>
            </Stack>

            {feature_license_management() && (
                <Fragment>
                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
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

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
            <Typography variant="h6" sx={{ marginBottom: 2 }}>
                Vulnerability scanning
            </Typography>

            <Stack direction="row" spacing={2} alignItems="center">
                <BooleanInput source="osv_enabled" label="OSV scanning enabled" defaultValue={true} />
                <FormDataConsumer>
                    {({ formData }) => formData.osv_enabled && <OSVLinuxDistributionInput />}
                </FormDataConsumer>
            </Stack>
            <FormDataConsumer>
                {({ formData }) =>
                    formData.osv_enabled && (
                        <Fragment>
                            {feature_automatic_osv_scanning() && (
                                <BooleanInput
                                    source="automatic_osv_scanning_enabled"
                                    label="Automatic OSV scanning enabled"
                                    defaultValue={false}
                                />
                            )}
                        </Fragment>
                    )
                }
            </FormDataConsumer>
        </Fragment>
    );
};
