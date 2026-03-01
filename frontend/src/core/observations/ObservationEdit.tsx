import { Divider, Stack, Typography } from "@mui/material";
import { useState } from "react";
import {
    DateInput,
    DeleteButton,
    Edit,
    FormDataConsumer,
    NumberInput,
    SaveButton,
    SimpleForm,
    TextInput,
    Toolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import observations from ".";
import { PERMISSION_OBSERVATION_DELETE } from "../../access_control/types";
import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import {
    validate_0_10,
    validate_0_999999,
    validate_255,
    validate_2048,
    validate_after_today,
    validate_required,
    validate_required_255,
} from "../../commons/custom_validators";
import { justificationIsEnabledForStatus, settings_vex_justification_style } from "../../commons/functions";
import { AutocompleteInputMedium, AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";
import { VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX, VEX_JUSTIFICATION_TYPE_CYCLONEDX } from "../../commons/types";
import {
    OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_CHOICES,
    OBSERVATION_STATUS_RISK_ACCEPTED,
    OBSERVATION_VEX_JUSTIFICATION_CHOICES,
} from "../../core/types";

const CustomToolbar = () => {
    const observation = useRecordContext();

    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            {observation?.product_data.permissions.includes(PERMISSION_OBSERVATION_DELETE) && (
                <DeleteButton mutationMode="pessimistic" />
            )}
        </Toolbar>
    );
};

interface ObservationEditFormProps {
    setDescription: (value: string) => void;
    setRecommendation: (value: string) => void;
}

const ObservationEditForm = ({ setDescription, setRecommendation }: ObservationEditFormProps) => {
    const observation = useRecordContext();
    const [status, setStatus] = useState(observation ? observation.parser_status : "");
    const justificationEnabled = justificationIsEnabledForStatus(status);
    const [descriptionSet, setDescriptionSet] = useState(false);
    const [recommendationSet, setRecommendationSet] = useState(false);

    if (!descriptionSet && observation) {
        setDescription(observation.description);
        setDescriptionSet(true);
    }
    if (!recommendationSet && observation) {
        setRecommendation(observation.recommendation);
        setRecommendationSet(true);
    }

    return (
        <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                <observations.icon />
                &nbsp;&nbsp;Observation
            </Typography>
            <Stack>
                <TextInputWide autoFocus source="title" validate={validate_required_255} />
                <Stack direction="row" spacing={2} alignItems="center">
                    <AutocompleteInputMedium
                        source="parser_severity"
                        label="Severity"
                        choices={OBSERVATION_SEVERITY_CHOICES}
                    />
                    <AutocompleteInputMedium
                        source="parser_status"
                        label="Status"
                        choices={OBSERVATION_STATUS_CHOICES}
                        validate={validate_required}
                        onChange={(e) => setStatus(e)}
                    />
                    <FormDataConsumer>
                        {({ formData }) =>
                            formData.parser_status &&
                            formData.parser_status == OBSERVATION_STATUS_RISK_ACCEPTED &&
                            formData.product_data.risk_acceptance_expiry_date_calculated && (
                                <DateInput
                                    source="risk_acceptance_expiry_date"
                                    label="Risk acceptance expiry date"
                                    defaultValue={formData.product_data.risk_acceptance_expiry_date_calculated}
                                    validate={validate_after_today()}
                                />
                            )
                        }
                    </FormDataConsumer>
                    {justificationEnabled &&
                        settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX && (
                            <AutocompleteInputWide
                                source="parser_vex_justification"
                                label="VEX justification"
                                choices={OBSERVATION_VEX_JUSTIFICATION_CHOICES}
                            />
                        )}
                    {justificationEnabled &&
                        settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CYCLONEDX && (
                            <AutocompleteInputWide
                                source="parser_vex_justification"
                                label="VEX justification"
                                choices={OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES}
                            />
                        )}
                </Stack>
                <MarkdownEdit
                    initialValue={observation ? observation.description : ""}
                    setValue={setDescription}
                    label="Description"
                    maxLength={2048}
                />
                <MarkdownEdit
                    initialValue={observation ? observation.recommendation : ""}
                    setValue={setRecommendation}
                    label="Recommendation"
                    maxLength={2048}
                />
            </Stack>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Product
            </Typography>
            <Stack>
                <TextInputWide source="product_data.name" label="Product" disabled />
                <WithRecord
                    render={(branch) => <BranchReferenceInput source="branch" product={branch.product_data.id} />}
                />
            </Stack>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Vulnerability
            </Typography>
            <Stack>
                <TextInputWide source="vulnerability_id" label="Vulnerability ID" validate={validate_255} />
                <Stack direction="row" spacing={2} alignItems="center">
                    <NumberInput
                        source="cvss4_score"
                        label="CVSS 4 score"
                        min={0}
                        step={0.1}
                        validate={validate_0_10}
                        sx={{ width: "10em" }}
                    />
                    <TextInputWide source="cvss4_vector" label="CVSS 4 vector" validate={validate_255} />
                    <TextUrlField
                        url="https://www.first.org/cvss/calculator/4.0"
                        text="CVSS 4 calculator"
                        new_tab={true}
                    />
                </Stack>
                <Stack direction="row" spacing={2} alignItems="center">
                    <NumberInput
                        source="cvss3_score"
                        label="CVSS 3 score"
                        min={0}
                        step={0.1}
                        validate={validate_0_10}
                        sx={{ width: "10em" }}
                    />
                    <TextInputWide source="cvss3_vector" label="CVSS 3 vector" validate={validate_255} />
                    <TextUrlField
                        url="https://www.first.org/cvss/calculator/3.1"
                        text="CVSS 3.1 calculator"
                        new_tab={true}
                    />
                </Stack>
                <NumberInput
                    source="cwe"
                    label="CWE"
                    min={0}
                    step={1}
                    validate={validate_0_999999}
                    sx={{ width: "10em" }}
                />
            </Stack>

            <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Origins
            </Typography>
            <Stack>
                <WithRecord
                    render={(service) => (
                        <ServiceReferenceInput source="origin_service" product={service.product_data.id} />
                    )}
                />
                <Stack direction="row" spacing={2}>
                    <TextInputWide source="origin_component_name" label="Component name" validate={validate_255} />
                    <TextInput source="origin_component_version" label="Component version" validate={validate_255} />
                </Stack>
                <Stack direction="row" spacing={2}>
                    <TextInputWide source="origin_docker_image_name" label="Container name" validate={validate_255} />
                    <TextInput source="origin_docker_image_tag" label="Container tag" validate={validate_255} />
                </Stack>
                <TextInputWide source="origin_endpoint_url" label="Endpoint URL" validate={validate_2048} />
                <Stack direction="row" spacing={2}>
                    <TextInputWide source="origin_source_file" label="Source file" validate={validate_255} />
                    <NumberInput
                        source="origin_source_line_start"
                        label="Source line start"
                        min={0}
                        step={1}
                        validate={validate_0_999999}
                    />
                    <NumberInput
                        source="origin_source_line_end"
                        label="Source line end"
                        min={0}
                        step={1}
                        validate={validate_0_999999}
                    />
                </Stack>
                <Stack direction="row" spacing={2}>
                    <TextInputWide source="origin_cloud_provider" label="Cloud provider" validate={validate_255} />
                    <TextInputWide
                        source="origin_cloud_account_subscription_project"
                        label="Account / Subscription / Project"
                        validate={validate_255}
                    />
                </Stack>
                <Stack direction="row" spacing={2}>
                    <TextInputWide
                        source="origin_cloud_resource_type"
                        label="Cloud resource type"
                        validate={validate_255}
                    />
                    <TextInputWide source="origin_cloud_resource" label="Cloud resource" validate={validate_255} />
                </Stack>
                <Stack direction="row" spacing={2}>
                    <TextInputWide
                        source="origin_kubernetes_cluster"
                        label="Kubernetes cluster"
                        validate={validate_255}
                    />
                    <TextInputWide source="origin_kubernetes_namespace" label="Namespace" validate={validate_255} />
                </Stack>
                <Stack direction="row" spacing={2}>
                    <TextInputWide
                        source="origin_kubernetes_resource_type"
                        label="Kubernetes resource type"
                        validate={validate_255}
                    />
                    <TextInputWide
                        source="origin_kubernetes_resource_name"
                        label="Kubernetes resource name"
                        validate={validate_255}
                    />
                </Stack>
            </Stack>
        </SimpleForm>
    );
};

const ObservationEdit = () => {
    const [description, setDescription] = useState("");
    const [recommendation, setRecommendation] = useState("");

    const transform = (data: any) => {
        data.description = description;
        data.recommendation = recommendation;

        data.parser_severity ??= "";
        data.origin_component_name ??= "";
        data.origin_component_version ??= "";
        data.origin_docker_image_name ??= "";
        data.origin_docker_image_tag ??= "";
        data.origin_endpoint_url ??= "";
        data.origin_source_file ??= "";
        data.origin_cloud_provider ??= "";
        data.origin_cloud_account_subscription_project ??= "";
        data.origin_cloud_resource ??= "";
        data.origin_cloud_resource_type ??= "";
        data.origin_kubernetes_cluster ??= "";
        data.origin_kubernetes_namespace ??= "";
        data.origin_kubernetes_resource_type ??= "";
        data.origin_kubernetes_resource_name ??= "";
        if (!justificationIsEnabledForStatus(data.parser_status) || !data.parser_vex_justification) {
            data.parser_vex_justification = "";
        }
        if (data.parser_status != OBSERVATION_STATUS_RISK_ACCEPTED) {
            data.risk_acceptance_expiry_date = null;
        }
        data.origin_component_name_version = "";
        data.origin_docker_image_name_tag = "";
        data.vulnerability_id ??= "";
        data.cvss3_vector ??= "";
        data.cvss4_vector ??= "";
        return data;
    };

    return (
        <Edit redirect="show" mutationMode="pessimistic" transform={transform}>
            <ObservationEditForm setDescription={setDescription} setRecommendation={setRecommendation} />
        </Edit>
    );
};

export default ObservationEdit;
