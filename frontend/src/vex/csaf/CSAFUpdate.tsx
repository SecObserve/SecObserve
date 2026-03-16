import EditIcon from "@mui/icons-material/Edit";
import { Dialog, DialogContent, DialogTitle, Divider, Typography } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useNotify, useRefresh } from "react-admin";

import axios_instance from "../../access_control/auth_provider/axios_instance";
import EditButton from "../../commons/custom_fields/EditButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../../commons/layout/themes";
import { CSAF_PUBLISHER_CATEGORY_CHOICES, CSAF_TLP_LABEL_CHOICES, CSAF_TRACKING_STATUS_CHOICES } from "../types";

const CSAFUpdate = () => {
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

    const update_csaf = async (data: any) => {
        setLoading(true);

        const url = "vex/csaf_document/update/" + data.document_id_prefix + "/" + data.document_base_id + "/";
        axios_instance
            .post(url, data, { responseType: "blob" })
            .then(function (response) {
                if (response.status == 204) {
                    setLoading(false);
                    notify("No changes in CSAF document", {
                        type: "warning",
                    });
                } else {
                    const blob = new Blob([response.data], { type: "application/json" });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = response.headers["content-disposition"].split("filename=")[1];
                    link.click();

                    refresh();
                    setLoading(false);
                    notify("CASF document updated", {
                        type: "success",
                    });
                }
                setOpen(false);
            })
            .catch(async function (error) {
                setLoading(false);
                notify(await error.response.data.text(), {
                    type: "warning",
                });
            });
    };

    return (
        <Fragment>
            <EditButton title="Update CSAF document" onClick={handleOpen} />
            <Dialog open={open && !loading} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Update CSAF document</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={update_csaf}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Update"
                                saveButtonIcon={<EditIcon />}
                                alwaysEnable
                            />
                        }
                    >
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Document
                        </Typography>
                        <AutocompleteInputMedium
                            source="tlp_label"
                            choices={CSAF_TLP_LABEL_CHOICES}
                            label="TLP label"
                            validate={validate_required}
                        />
                        <Divider flexItem sx={{ marginBottom: 2 }} />
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Tracking and Publisher
                        </Typography>
                        <AutocompleteInputMedium
                            source="tracking_status"
                            choices={CSAF_TRACKING_STATUS_CHOICES}
                            validate={validate_required}
                        />
                        <TextInputWide source="publisher_name" validate={validate_required_255} />
                        <AutocompleteInputMedium
                            source="publisher_category"
                            choices={CSAF_PUBLISHER_CATEGORY_CHOICES}
                            validate={validate_required}
                        />
                        <TextInputWide source="publisher_namespace" validate={validate_required_255} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={open && loading} />
        </Fragment>
    );
};

export default CSAFUpdate;
