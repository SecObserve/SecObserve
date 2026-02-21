import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useEffect, useState } from "react";
import {
    BooleanInput,
    ReferenceInput,
    SimpleForm,
    WithRecord,
    useDataProvider,
    useNotify,
    useRefresh,
    useUpdate,
} from "react-admin";
import { useWatch } from "react-hook-form";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import EditButton from "../../commons/custom_fields/EditButton";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import {
    validate_255,
    validate_513,
    validate_2048,
    validate_required,
    validate_required_255,
} from "../../commons/custom_validators";
import { feature_automatic_api_import } from "../../commons/functions";
import { AutocompleteInputWide, PasswordInputWide, TextInputWide } from "../../commons/layout/themes";

const ApiConfigurationEdit = () => {
    const [open, setOpen] = useState(false);
    const [parsers, setParsers] = useState<any[]>([]);
    const [update] = useUpdate();
    const refresh = useRefresh();
    const notify = useNotify();
    const dataProvider = useDataProvider();

    useEffect(() => {
        // Fetch the list of parsers from the backend
        dataProvider
            .getList("parsers", {
                pagination: { page: 1, perPage: 100 },
                sort: { field: "name", order: "ASC" },
                filter: { source: "API" },
            })
            .then(({ data }) => {
                setParsers(data);
            })
            .catch((error) => {
                notify(`Error fetching parsers: ${error.message}`, { type: "warning" });
            });
    }, [dataProvider, notify]);

    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason === "backdropClick") return;
        setOpen(false);
    };

    const api_configuration_update = async (data: any) => {
        const patch = {
            name: data.name,
            parser: data.parser,
            base_url: data.base_url,
            project_key: data.project_key,
            api_key: data.api_key,
            test_connection: data.test_connection,
            query: data.query,
            basic_auth_enabled: data.basic_auth_enabled,
            basic_auth_username: data.basic_auth_username,
            basic_auth_password: data.basic_auth_password,
            verify_ssl: data.verify_ssl,
            automatic_import_enabled: data.automatic_import_enabled,
            automatic_import_branch: data.automatic_import_branch,
            automatic_import_service: data.automatic_import_service,
            automatic_import_docker_image_name_tag: data.automatic_import_docker_image_name_tag,
            automatic_import_endpoint_url: data.automatic_import_endpoint_url,
            automatic_import_kubernetes_cluster: data.automatic_import_kubernetes_cluster,
        };

        if (!patch.base_url) {
            patch.base_url = "";
        }
        if (!patch.project_key) {
            patch.project_key = "";
        }
        if (!patch.api_key) {
            patch.api_key = "";
        }
        if (!patch.query) {
            patch.query = "";
        }
        if (!patch.basic_auth_username) {
            patch.basic_auth_username = "";
        }
        if (!patch.basic_auth_password) {
            patch.basic_auth_password = "";
        }
        if (!patch.automatic_import_service) {
            patch.automatic_import_service = "";
        }
        if (!patch.automatic_import_docker_image_name_tag) {
            patch.automatic_import_docker_image_name_tag = "";
        }
        if (!patch.automatic_import_endpoint_url) {
            patch.automatic_import_endpoint_url = "";
        }
        if (!patch.automatic_import_kubernetes_cluster) {
            patch.automatic_import_kubernetes_cluster = "";
        }

        update(
            "api_configurations",
            {
                id: data.id,
                data: patch,
            },
            {
                onSuccess: () => {
                    refresh();
                    notify("API configuration updated", {
                        type: "success",
                    });
                    setOpen(false);
                },
                onError: (error: any) => {
                    notify(error.message, {
                        type: "warning",
                    });
                },
            }
        );
    };

    const ParserInput = () => {
        const parserId = useWatch({ name: "parser" });
        const selectedParser = parsers.find((parser) => parser.id === parserId);
        if (selectedParser) {
            switch (selectedParser.name) {
                case "Dependency Track":
                    return (
                        <>
                            <TextInputWide source="api_key" label="API key" validate={validate_required_255} />
                            <TextInputWide source="project_key" validate={validate_required_255} />
                        </>
                    );
                case "Trivy Operator Prometheus":
                    return (
                        <>
                            <TextInputWide source="query" label="Query" validate={validate_required_255} />
                            <BooleanInput
                                source="basic_auth_enabled"
                                label="Basic authentication"
                                defaultValue={false}
                            />
                            <BasicAuthInput />
                        </>
                    );
            }
        } else {
            return null;
        }
    };

    const BasicAuthInput = () => {
        const basic_auth_enabledId = useWatch({ name: "basic_auth_enabled" });
        if (basic_auth_enabledId) {
            return (
                <>
                    <TextInputWide source="basic_auth_username" label="Username" validate={validate_required_255} />
                    <PasswordInputWide source="basic_auth_password" label="Password" validate={validate_required_255} />
                </>
            );
        } else {
            return null;
        }
    };

    const AutomaticImportInput = () => {
        const automatic_import_enabled = useWatch({ name: "automatic_import_enabled" });
        if (automatic_import_enabled) {
            return (
                <WithRecord
                    render={(api_configuration) => (
                        <Fragment>
                            <BranchReferenceInput
                                source="automatic_import_branch"
                                product={api_configuration.product}
                            />
                            <ServiceReferenceInput
                                source="automatic_import_service"
                                product={api_configuration.product}
                            />
                            <TextInputWide
                                source="automatic_import_docker_image_name_tag"
                                label="Docker image name:tag"
                                validate={validate_513}
                            />
                            <TextInputWide
                                label="Endpoint URL"
                                source="automatic_import_endpoint_url"
                                validate={validate_2048}
                            />
                            <TextInputWide
                                label="Kubernetes cluster"
                                source="automatic_import_kubernetes_cluster"
                                validate={validate_255}
                            />
                        </Fragment>
                    )}
                />
            );
        } else {
            return null;
        }
    };

    return (
        <Fragment>
            <EditButton title="Edit" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Edit API configuration</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={api_configuration_update}
                        toolbar={<ToolbarCancelSave onClick={handleCancel} />}
                    >
                        <TextInputWide autoFocus source="name" validate={validate_required_255} />
                        <ReferenceInput
                            source="parser"
                            reference="parsers"
                            sort={{ field: "name", order: "ASC" }}
                            filter={{ source: "API" }}
                        >
                            <AutocompleteInputWide optionText="name" validate={validate_required} />
                        </ReferenceInput>
                        <TextInputWide source="base_url" label="Base URL" validate={validate_required_255} />
                        <ParserInput />
                        <BooleanInput source="verify_ssl" label="Verify SSL" defaultValue={true} />
                        {feature_automatic_api_import() && (
                            <Fragment>
                                <BooleanInput source="automatic_import_enabled" defaultValue={false} />
                                <AutomaticImportInput />
                            </Fragment>
                        )}
                        <BooleanInput source="test_connection" defaultValue={true} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ApiConfigurationEdit;
