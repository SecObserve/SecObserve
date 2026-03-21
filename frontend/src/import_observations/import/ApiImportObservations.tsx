import UploadIcon from "@mui/icons-material/CloudUpload";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { ReferenceInput, SimpleForm, useNotify, useRefresh } from "react-admin";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import MenuButton from "../../commons/custom_fields/MenuButton";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_255, validate_513, validate_2048, validate_required } from "../../commons/custom_validators";
import { getIconAndFontColor } from "../../commons/functions";
import { AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

const ApiImportObservations = (product: any) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => {
        setOpen(false);
        setLoading(false);
    };
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
        setLoading(false);
    };

    const observationUpdate = async (data: any) => {
        setLoading(true);

        const formData: any = {
            api_configuration: data.api_configuration,
            parser: data.parser,
        };
        if (data.branch) {
            formData.branch = data.branch;
        }
        if (data.service_id) {
            formData.service_id = data.service_id;
        }
        if (data.docker_image_name_tag) {
            formData.docker_image_name_tag = data.docker_image_name_tag;
        }
        if (data.endpoint_url) {
            formData.endpoint_url = data.endpoint_url;
        }
        if (data.kubernetes_cluster) {
            formData.kubernetes_cluster = data.kubernetes_cluster;
        }

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/import/api_import_observations_by_id/", {
            method: "POST",
            body: JSON.stringify(formData),
        })
            .then((result) => {
                const message =
                    result.json.observations_new +
                    " new observations\n" +
                    result.json.observations_updated +
                    " updated observations\n" +
                    result.json.observations_resolved +
                    " resolved observations";
                refresh();
                setLoading(false);
                setOpen(false);
                notify(message, {
                    type: "success",
                });
            })
            .catch((error) => {
                setLoading(false);
                setOpen(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    return (
        <Fragment>
            <MenuButton
                title="Import observations from API"
                onClick={handleOpen}
                icon={<UploadIcon sx={{ color: getIconAndFontColor() }} />}
            />
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle>Import observations from API</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={observationUpdate}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Import"
                                saveButtonIcon={<UploadIcon />}
                            />
                        }
                    >
                        <ReferenceInput
                            source="api_configuration"
                            reference="api_configurations"
                            sort={{ field: "name", order: "ASC" }}
                            filter={{ product: product.product.id }}
                        >
                            <AutocompleteInputWide
                                optionText="name"
                                label="API configuration"
                                validate={validate_required}
                            />
                        </ReferenceInput>
                        {product.product.has_branches && (
                            <BranchReferenceInput
                                source="branch"
                                product={product.product.id}
                                defaultValue={product.product.repository_default_branch}
                            />
                        )}
                        {product.product.has_services && (
                            <ServiceReferenceInput source="service_id" product={product.product.id} />
                        )}
                        <TextInputWide
                            source="docker_image_name_tag"
                            label="Docker image name:tag"
                            validate={validate_513}
                        />
                        <TextInputWide label="Endpoint URL" source="endpoint_url" validate={validate_2048} />
                        <TextInputWide source="kubernetes_cluster" validate={validate_255} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={open && loading} />
        </Fragment>
    );
};

export default ApiImportObservations;
