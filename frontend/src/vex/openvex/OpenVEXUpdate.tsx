import EditIcon from "@mui/icons-material/Edit";
import { Dialog, DialogContent, DialogTitle, Typography } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useNotify, useRefresh } from "react-admin";

import axios_instance from "../../access_control/auth_provider/axios_instance";
import EditButton from "../../commons/custom_fields/EditButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required_255 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";

const OpenVEXUpdate = () => {
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

    const update_openvex = async (data: any) => {
        setLoading(true);

        const url = "vex/openvex_document/update/" + data.document_id_prefix + "/" + data.document_base_id + "/";
        axios_instance
            .post(url, data, { responseType: "blob" })
            .then(function (response) {
                if (response.status == 204) {
                    setLoading(false);
                    notify("No changes in OpenVEX document", {
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
                    notify("OpenVEX document updated", {
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
            <EditButton title="Update OpenVEX document" onClick={handleOpen} />
            <Dialog open={open && !loading} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Update OpenVEX document</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={update_openvex}
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
                        <TextInputWide source="author" validate={validate_required_255} autoFocus />
                        <TextInputWide source="role" validate={validate_required_255} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={open && loading} />
        </Fragment>
    );
};

export default OpenVEXUpdate;
