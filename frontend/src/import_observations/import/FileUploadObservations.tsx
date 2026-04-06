import UploadIcon from "@mui/icons-material/Upload";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { FileField, FileInput, SimpleForm, WithRecord, useNotify, useRefresh } from "react-admin";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import MenuButton from "../../commons/custom_fields/MenuButton";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_255, validate_513, validate_2048, validate_required } from "../../commons/custom_validators";
import { getIconAndFontColor } from "../../commons/functions";
import { TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

const FileUploadObservations = () => {
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

        let new_observations = 0;
        let updated_observations = 0;
        let resolved_observations = 0;

        let upload_error = false;
        let error_message = "";
        let error_sbom = "";

        for (const file of data.file) {
            const formData = new FormData();
            formData.append("file", file.rawFile, file.title);
            formData.append("product", data.id);
            if (data.branch) {
                formData.append("branch", data.branch);
            }
            if (data.service_id) {
                formData.append("service_id", data.service_id);
            }
            if (data.docker_image_name_tag) {
                formData.append("docker_image_name_tag", data.docker_image_name_tag);
            }
            if (data.endpoint_url) {
                formData.append("endpoint_url", data.endpoint_url);
            }
            if (data.kubernetes_cluster) {
                formData.append("kubernetes_cluster", data.kubernetes_cluster);
            }
            formData.append("suppress_licenses", "true");

            await httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/import/file_upload_observations_by_id/", {
                method: "POST",
                body: formData,
            })
                .then((result) => {
                    new_observations += result.json.observations_new;
                    updated_observations += result.json.observations_updated;
                    resolved_observations += result.json.observations_resolved;
                })
                .catch((error) => {
                    upload_error = true;
                    error_message = error.message;
                    error_sbom = file.title;
                });

            if (upload_error) {
                break;
            }
        }

        setLoading(false);
        setOpen(false);
        refresh();

        if (upload_error) {
            notify("Error '" + error_message + "' while processing '" + error_sbom + "'", { type: "warning" });
        } else {
            const message =
                new_observations +
                " new observations\n" +
                updated_observations +
                " updated observations\n" +
                resolved_observations +
                " resolved observations";
            notify(message, {
                type: "success",
                multiLine: true,
            });
        }
    };

    return (
        <Fragment>
            <MenuButton
                title="Upload observations from files"
                onClick={handleOpen}
                icon={<UploadIcon sx={{ color: getIconAndFontColor() }} />}
            />
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle>Upload observations from files</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={observationUpdate}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Upload"
                                saveButtonIcon={<UploadIcon />}
                            />
                        }
                    >
                        <FileInput
                            source="file"
                            label="Scan reports  (max 10 files)"
                            accept={{ "application/octet-stream": [".csv, .json, .sarif"] }}
                            validate={validate_required}
                            multiple={true}
                            options={{ maxFiles: 10 }}
                            placeholder={<p>Drop some files to upload, or click to select some.</p>}
                            au
                        >
                            <FileField source="src" title="title" />
                        </FileInput>
                        <WithRecord
                            render={(product) => (
                                <Fragment>
                                    {product.has_branches && (
                                        <BranchReferenceInput
                                            source="branch"
                                            product={product.id}
                                            defaultValue={product.repository_default_branch}
                                        />
                                    )}
                                    {product.has_services && (
                                        <ServiceReferenceInput source="service_id" product={product.id} />
                                    )}
                                </Fragment>
                            )}
                        />
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

export default FileUploadObservations;
