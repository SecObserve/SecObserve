import UploadIcon from "@mui/icons-material/Upload";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { FileField, FileInput, SimpleForm, useNotify, useRefresh } from "react-admin";

import SmallButton from "../../commons/custom_fields/SmallButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required } from "../../commons/custom_validators";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

const VEXDocumentImport = () => {
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

    const vexImport = async (data: any) => {
        setLoading(true);

        const formData = new FormData();
        formData.append("file", data.file.rawFile, data.file.title);

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/vex/vex_import/", {
            method: "POST",
            body: formData,
        })
            .then(() => {
                refresh();
                setLoading(false);
                setOpen(false);
                notify("VEX document imported", {
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
            <SmallButton title="Import VEX document" onClick={handleOpen} icon={<UploadIcon />} />
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle>Import VEX document</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={vexImport}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Import"
                                saveButtonIcon={<UploadIcon />}
                            />
                        }
                    >
                        <FileInput
                            source="file"
                            label="VEX document"
                            accept={{ "application/octet-stream": [".json"] }}
                            validate={validate_required}
                        >
                            <FileField source="src" title="title" />
                        </FileInput>
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={open && loading} />
        </Fragment>
    );
};

export default VEXDocumentImport;
