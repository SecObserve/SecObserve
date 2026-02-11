import { Box, Divider, Paper, Stack, Typography } from "@mui/material";
import { RefObject } from "react";
import { Fragment, useState } from "react";
import {
    BooleanField,
    BooleanInput,
    ChipField,
    DateField,
    Labeled,
    ReferenceField,
    ReferenceInput,
    TextField,
    useRecordContext,
} from "react-admin";
import { useWatch } from "react-hook-form";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import rego from "react-syntax-highlighter/dist/esm/languages/prism/rego";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

import MarkdownEdit from "../commons/custom_fields/MarkdownEdit";
import MarkdownField from "../commons/custom_fields/MarkdownField";
import TextUrlField from "../commons/custom_fields/TextUrlField";
import {
    validate_255,
    validate_513,
    validate_2048,
    validate_required,
    validate_required_255,
} from "../commons/custom_validators";
import {
    feature_general_rules_need_approval_enabled,
    feature_vex_enabled,
    justificationIsEnabledForStatus,
    settings_vex_justification_style,
} from "../commons/functions";
import {
    AutocompleteInputMedium,
    AutocompleteInputWide,
    TextInputExtraWide,
    TextInputWide,
    useStyles,
} from "../commons/layout/themes";
import { VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX, VEX_JUSTIFICATION_TYPE_CYCLONEDX } from "../commons/types";
import { getResolvedSettingTheme } from "../commons/user_settings/functions";
import {
    OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_CHOICES,
    OBSERVATION_VEX_JUSTIFICATION_CHOICES,
} from "../core/types";
import general_rules from "./general_rules";
import product_rules from "./product_rules";
import { RULE_TYPE_CHOICES, RULE_TYPE_FIELDS, RULE_TYPE_REGO } from "./types";

SyntaxHighlighter.registerLanguage("rego", rego);

export function getRegoTheme() {
    const theme = getResolvedSettingTheme();
    if (theme === "dark") {
        return oneDark;
    } else {
        return oneLight;
    }
}

export const validateRuleForm = (values: any) => {
    const errors: any = {};

    if (!values.name) {
        errors.name = "Name is required";
    }

    if (values.type === RULE_TYPE_FIELDS) {
        if (!values.new_severity && !values.new_status) {
            errors.new_severity = "Either New severity or New status must be set";
            errors.new_status = "Either New severity or New status must be set";
        }

        if (!values.parser && !values.scanner_prefix) {
            errors.parser = "Either Parser or Scanner prefix must be set";
            errors.scanner_prefix = "Either Parser or Scanner prefix must be set";
        }
    }

    if (values.type === RULE_TYPE_REGO) {
        if (!values.rego_module) {
            errors.rego_module = "Rego module is required";
        }
    }

    console.log(errors);

    return errors;
};

function generateProductURL(product_id: number, is_product_group: boolean): string {
    if (is_product_group) {
        return "#/product_groups/" + product_id + "/show/rules";
    }
    return "#/products/" + product_id + "/show/rules";
}

function getProductLabel(product_data: any): string {
    if (product_data.is_product_group) {
        return "Product group";
    }
    return "Product";
}

export const RuleShowComponent = ({ rule }: any) => {
    const { classes } = useStyles();

    return (
        <Box width={"100%"}>
            <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                {rule.product_data && (
                    <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                        <product_rules.icon />
                        &nbsp;&nbsp;Product Rule
                    </Typography>
                )}
                {!rule.product_data && (
                    <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                        <general_rules.icon />
                        &nbsp;&nbsp;General Rule
                    </Typography>
                )}
                <Stack spacing={1}>
                    {rule.product_data && (
                        <Labeled>
                            <TextUrlField
                                label={getProductLabel(rule.product_data)}
                                text={rule.product_data.name}
                                url={generateProductURL(rule.product_data.id, rule.product_data.is_product_group)}
                            />
                        </Labeled>
                    )}
                    <Labeled label="Name">
                        <TextField source="name" className={classes.fontBigBold} />
                    </Labeled>
                    {rule.description && (
                        <Labeled>
                            <MarkdownField content={rule.description} label="Description" />
                        </Labeled>
                    )}

                    <Labeled label="Type">
                        <ChipField
                            source="type"
                            sx={{
                                width: "fit-content",
                            }}
                        />
                    </Labeled>

                    {rule.new_severity && (
                        <Labeled label="New severity">
                            <TextField source="new_severity" />
                        </Labeled>
                    )}
                    {rule.new_status && (
                        <Labeled label="New status">
                            <TextField source="new_status" />
                        </Labeled>
                    )}
                    {feature_vex_enabled() && rule.new_vex_justification && (
                        <Labeled label="New VEX justification">
                            <TextField source="new_vex_justification" />
                        </Labeled>
                    )}

                    {rule.rego_module && (
                        <Labeled label="Rego module">
                            <SyntaxHighlighter
                                language="javascript"
                                style={getRegoTheme()}
                                wrapLongLines
                                customStyle={{ lineHeight: "1.43", fontSize: "0.875rem" }}
                                codeTagProps={{
                                    style: {
                                        lineHeight: "inherit",
                                        fontSize: "inherit",
                                    },
                                }}
                            >
                                {rule.rego_module}
                            </SyntaxHighlighter>
                        </Labeled>
                    )}

                    <Labeled label="Enabled">
                        <BooleanField source="enabled" />
                    </Labeled>
                    {rule.user_full_name && (
                        <Labeled label="Last changed by">
                            <TextField source="user_full_name" />
                        </Labeled>
                    )}
                </Stack>
            </Paper>

            {rule && (rule.parser || rule.scanner_prefix || rule.title || rule.description_observation) && (
                <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Observation
                    </Typography>
                    <Stack spacing={1}>
                        {rule.parser && (
                            <Labeled label="Parser">
                                <ReferenceField
                                    source="parser"
                                    reference="parsers"
                                    link="show"
                                    sx={{ "& a": { textDecoration: "none" } }}
                                />
                            </Labeled>
                        )}
                        {rule.scanner_prefix && (
                            <Labeled label="Scanner prefix">
                                <TextField source="scanner_prefix" />
                            </Labeled>
                        )}
                        {rule.title && (
                            <Labeled label="Title">
                                <TextField source="title" />
                            </Labeled>
                        )}
                        {rule.description_observation && (
                            <Labeled label="Description">
                                <TextField source="description_observation" />
                            </Labeled>
                        )}
                    </Stack>
                </Paper>
            )}

            {rule &&
                (rule.origin_component_name_version ||
                    rule.origin_component_purl ||
                    rule.origin_docker_image_name_tag ||
                    rule.origin_endpoint_url ||
                    rule.origin_service_name ||
                    rule.origin_source_file ||
                    rule.origin_cloud_qualified_resource ||
                    rule.origin_kubernetes_qualified_resource) && (
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Origins
                        </Typography>
                        <Stack spacing={1}>
                            {rule.origin_component_name_version && (
                                <Labeled label="Component name:version">
                                    <TextField source="origin_component_name_version" />
                                </Labeled>
                            )}
                            {rule.origin_component_purl && (
                                <Labeled label="Component PURL">
                                    <TextField source="origin_component_purl" />
                                </Labeled>
                            )}
                            {rule.origin_docker_image_name_tag && (
                                <Labeled label="Docker image name:tag">
                                    <TextField source="origin_docker_image_name_tag" />
                                </Labeled>
                            )}
                            {rule.origin_endpoint_url && (
                                <Labeled label="Endpoint URL">
                                    <TextField source="origin_endpoint_url" />
                                </Labeled>
                            )}
                            {rule.origin_service_name && (
                                <Labeled label="Service name">
                                    <TextField source="origin_service_name" />
                                </Labeled>
                            )}
                            {rule.origin_source_file && (
                                <Labeled label="Source file">
                                    <TextField source="origin_source_file" />
                                </Labeled>
                            )}
                            {rule.origin_cloud_qualified_resource && (
                                <Labeled label="Cloud qualified resource">
                                    <TextField source="origin_cloud_qualified_resource" />
                                </Labeled>
                            )}
                            {rule.origin_kubernetes_qualified_resource && (
                                <Labeled label="Kubernetes qualified resource">
                                    <TextField source="origin_kubernetes_qualified_resource" />
                                </Labeled>
                            )}
                        </Stack>
                    </Paper>
                )}

            {((rule.product_data &&
                (rule.product_data.product_rules_need_approval ||
                    rule.product_data.product_group_product_rules_need_approval)) ||
                (!rule.product_data && feature_general_rules_need_approval_enabled())) && (
                <Paper sx={{ marginBottom: 1, padding: 2, width: "100%" }}>
                    <Typography variant="h6" sx={{ marginBottom: 1 }}>
                        Approval
                    </Typography>
                    <Stack spacing={1}>
                        <Labeled label="Status">
                            <ChipField
                                source="approval_status"
                                sx={{
                                    width: "fit-content",
                                }}
                            />
                        </Labeled>
                        {rule.approval_user_full_name && (
                            <Labeled label="Approved/rejected by">
                                <TextField source="approval_user_full_name" />
                            </Labeled>
                        )}
                        {rule.approval_remark && (
                            <Labeled label="Approval/rejection remark">
                                <TextField source="approval_remark" />
                            </Labeled>
                        )}
                        {rule.approval_date && (
                            <Labeled label="Approval/rejection date">
                                <DateField source="approval_date" showTime />
                            </Labeled>
                        )}
                    </Stack>
                </Paper>
            )}
        </Box>
    );
};

export const non_duplicate_transform = (data: any, description: string) => {
    data.description = description;
    data.type ??= "";

    if (data.type === RULE_TYPE_FIELDS) {
        data.title ??= "";
        data.description_observation ??= "";
        data.new_severity ??= "";
        data.new_status ??= "";
        if (!justificationIsEnabledForStatus(data.new_status) || data.new_vex_justification == null) {
            data.new_vex_justification = "";
        }

        data.scanner_prefix ??= "";

        data.origin_component_name_version ??= "";
        data.origin_component_purl ??= "";
        data.origin_docker_image_name_tag ??= "";
        data.origin_endpoint_url ??= "";
        data.origin_service_name ??= "";
        data.origin_source_file ??= "";
        data.origin_cloud_qualified_resource ??= "";
        data.origin_kubernetes_qualified_resource ??= "";

        data.rego_module = "";
    }

    if (data.type === RULE_TYPE_REGO) {
        data.title = "";
        data.description_observation = "";
        data.new_severity = "";
        data.new_status = "";
        data.new_vex_justification = "";

        data.scanner_prefix = "";

        data.origin_component_name_version = "";
        data.origin_component_purl = "";
        data.origin_docker_image_name_tag = "";
        data.origin_endpoint_url = "";
        data.origin_service_name = "";
        data.origin_source_file = "";
        data.origin_cloud_qualified_resource = "";
        data.origin_kubernetes_qualified_resource = "";

        data.rego_module ??= "";
    }

    return data;
};

interface SeverityStatusInputProps {
    initialStatus: string;
}

const SeverityStatusInput = ({ initialStatus }: SeverityStatusInputProps) => {
    const [status, setStatus] = useState(initialStatus);
    const justificationEnabled = justificationIsEnabledForStatus(status);
    const type = useWatch({ name: "type" });

    if (type === RULE_TYPE_FIELDS) {
        return (
            <Fragment>
                <AutocompleteInputMedium source="new_severity" choices={OBSERVATION_SEVERITY_CHOICES} />
                <AutocompleteInputMedium
                    source="new_status"
                    choices={OBSERVATION_STATUS_CHOICES}
                    onChange={(e) => setStatus(e)}
                />
                {justificationEnabled && settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX && (
                    <AutocompleteInputWide
                        source="new_vex_justification"
                        label="New VEX justification"
                        choices={OBSERVATION_VEX_JUSTIFICATION_CHOICES}
                    />
                )}
                {justificationEnabled && settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CYCLONEDX && (
                    <AutocompleteInputWide
                        source="new_vex_justification"
                        label="New VEX justification"
                        choices={OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES}
                    />
                )}
            </Fragment>
        );
    } else {
        return null;
    }
};

const RegoModuleInput = () => {
    const type = useWatch({ name: "type" });

    if (type === RULE_TYPE_REGO) {
        return (
            <Stack sx={{ marginBottom: 2 }}>
                <TextInputExtraWide multiline={true} source="rego_module" validate={validate_required} minRows={3} />
                <TextUrlField url="https://play.openpolicyagent.org/" text="Rego playground" new_tab={true} />
            </Stack>
        );
    } else {
        return null;
    }
};

const FieldsInput = () => {
    const type = useWatch({ name: "type" });

    if (type === RULE_TYPE_FIELDS) {
        return (
            <Fragment>
                <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

                <Typography variant="h6" sx={{ marginBottom: 1 }}>
                    Observation
                </Typography>
                <Stack>
                    <ReferenceInput source="parser" reference="parsers" sort={{ field: "name", order: "ASC" }}>
                        <AutocompleteInputWide optionText="name" />
                    </ReferenceInput>
                    <TextInputWide source="scanner_prefix" validate={validate_255} />
                    <TextInputWide
                        source="title"
                        label="Title"
                        helperText="Regular expression to match the observation's title"
                        validate={validate_255}
                    />
                    <TextInputWide
                        source="description_observation"
                        label="Description"
                        helperText="Regular expression to match the observation's description"
                        validate={validate_255}
                    />
                </Stack>

                <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

                <Typography variant="h6" sx={{ marginBottom: 1 }}>
                    Origins
                </Typography>
                <Stack>
                    <TextInputWide
                        source="origin_component_name_version"
                        label="Component name:version"
                        helperText="Regular expression to match the component name:version"
                        validate={validate_513}
                    />
                    <TextInputWide
                        source="origin_component_purl"
                        label="Component PURL"
                        helperText="Regular expression to match the component PURL"
                        validate={validate_255}
                    />
                    <TextInputWide
                        source="origin_docker_image_name_tag"
                        label="Docker image name:tag"
                        helperText="Regular expression to match the docker image name:tag"
                        validate={validate_513}
                    />
                    <TextInputWide
                        source="origin_endpoint_url"
                        label="Endpoint URL"
                        helperText="Regular expression to match the endpoint URL"
                        validate={validate_2048}
                    />
                    <TextInputWide
                        source="origin_service_name"
                        label="Service name"
                        helperText="Regular expression to match the service name"
                        validate={validate_255}
                    />
                    <TextInputWide
                        source="origin_source_file"
                        label="Source file"
                        helperText="Regular expression to match the source file"
                        validate={validate_255}
                    />
                    <TextInputWide
                        source="origin_cloud_qualified_resource"
                        label="Cloud qualified resource"
                        helperText="Regular expression to match the cloud qualified resource name"
                        validate={validate_255}
                    />
                    <TextInputWide
                        source="origin_kubernetes_qualified_resource"
                        label="Kubernetes qualified resource"
                        helperText="Regular expression to match the Kubernetes qualified resource name"
                        validate={validate_255}
                    />
                </Stack>
            </Fragment>
        );
    } else {
        return null;
    }
};

interface RuleCreateEditComponentProps {
    product: any;
    initialStatus: string;
    initialDescription: string;
    setDescription: (value: string) => void;
    dialogRef?: RefObject<HTMLDivElement | null> | null;
}

export const RuleCreateEditComponent = ({
    product,
    initialStatus,
    initialDescription,
    setDescription,
    dialogRef = null,
}: RuleCreateEditComponentProps) => {
    return (
        <Fragment>
            {product && (
                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                    <product_rules.icon />
                    &nbsp;&nbsp;Product Rule
                </Typography>
            )}
            {!product && (
                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                    <general_rules.icon />
                    &nbsp;&nbsp;General Rule
                </Typography>
            )}
            <Stack>
                {product && (
                    <TextInputWide source="product_name" defaultValue={product.name} label="Product" disabled />
                )}
                <TextInputWide autoFocus source="name" validate={validate_required_255} />
                <MarkdownEdit
                    initialValue={initialDescription}
                    setValue={setDescription}
                    label="Description"
                    maxLength={2048}
                    overlayContainer={dialogRef?.current ?? null}
                />

                <AutocompleteInputMedium source="type" choices={RULE_TYPE_CHOICES} validate={validate_required} />
                <SeverityStatusInput initialStatus={initialStatus} />
                <RegoModuleInput />

                <BooleanInput source="enabled" defaultValue={true} />
            </Stack>

            <FieldsInput />
        </Fragment>
    );
};

interface RuleEditComponentProps {
    product: any;
    initialStatus: string;
    setDescription: (value: string) => void;
}

export const RuleEditComponent = ({ product, initialStatus, setDescription }: RuleEditComponentProps) => {
    const rule = useRecordContext();
    const [descriptionSet, setDescriptionSet] = useState(false);
    const [initialDescription, setInitialDescription] = useState("");

    if (!descriptionSet && rule) {
        setInitialDescription(rule.description || "");
        setDescription(rule.description);
        setDescriptionSet(true);
    }

    return (
        <RuleCreateEditComponent
            product={product}
            initialStatus={initialStatus}
            initialDescription={initialDescription}
            setDescription={setDescription}
        />
    );
};
