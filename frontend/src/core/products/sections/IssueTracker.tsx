import { Stack } from "@mui/material";
import { BooleanField, BooleanInput, FormDataConsumer, Labeled, TextField, useRecordContext } from "react-admin";

import { SeverityField } from "../../../commons/custom_fields/SeverityField";
import { validate_255 } from "../../../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../../../commons/layout/themes";
import { ISSUE_TRACKER_TYPE_CHOICES, OBSERVATION_SEVERITY_CHOICES } from "../../types";

export const IssueTrackerInputs = () => (
    <>
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
                        <TextInputWide source="issue_tracker_project_id" label="Project id" validate={validate_255} />
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
    </>
);

export const isIssueTrackerVisible = (product: any) => Boolean(product.issue_tracker_active);

export const IssueTrackerFields = () => {
    const product: any = useRecordContext();
    if (!product) {
        return null;
    }

    return (
        <>
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
        </>
    );
};
