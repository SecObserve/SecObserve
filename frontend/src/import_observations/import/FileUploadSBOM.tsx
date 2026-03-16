import UploadIcon from "@mui/icons-material/Upload";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { FileField, FileInput, SimpleForm, WithRecord, useNotify, useRefresh } from "react-admin";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import MenuButton from "../../commons/custom_fields/MenuButton";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required } from "../../commons/custom_validators";
import { getIconAndFontColor } from "../../commons/functions";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

const FileUploadSBOM = () => {
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

    const uploadSBOM = async (data: any) => {
        setLoading(true);

        let new_license_components = 0;
        let updated_license_components = 0;
        let deleted_license_components = 0;

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

            await httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/import/file_upload_sbom_by_id/", {
                method: "POST",
                body: formData,
            })
                .then((result) => {
                    new_license_components += result.json.license_components_new;
                    updated_license_components += result.json.license_components_updated;
                    deleted_license_components += result.json.license_components_deleted;
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
                new_license_components +
                " new license components\n" +
                updated_license_components +
                " updated license components\n" +
                deleted_license_components +
                " deleted license components";
            notify(message, {
                type: "success",
                multiLine: true,
            });
        }
    };

    return (
        <Fragment>
            <MenuButton
                title="Upload SBOMs from files"
                onClick={handleOpen}
                icon={<UploadIcon sx={{ color: getIconAndFontColor() }} />}
            />
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle>Upload SBOMs from files</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={uploadSBOM}
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
                            label="SBOMs (max 10 files)"
                            accept={{ "application/octet-stream": [".json"] }}
                            validate={validate_required}
                            multiple={true}
                            options={{ maxFiles: 10 }}
                            placeholder={<p>Drop some files to upload, or click to select some.</p>}
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
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={open && loading} />
        </Fragment>
    );
};

export default FileUploadSBOM;
