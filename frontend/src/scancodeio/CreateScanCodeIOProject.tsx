import AddCircleIcon from "@mui/icons-material/AddCircle";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useNotify } from "react-admin";

import MenuButton from "../commons/custom_fields/MenuButton";
import { Spinner } from "../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../commons/custom_fields/ToolbarCancelSave";
import { getIconAndFontColor } from "../commons/functions";
import { httpClient } from "../commons/ra-data-django-rest-framework";

interface CreateScanCodeIOProjectProps {
    product: any;
}

const CreateScanCodeIOProject = ({ product }: CreateScanCodeIOProjectProps) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
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

    const createScanCodeIOProject = async () => {
        setLoading(true);

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/products/" + product.id + "/create_scancodeio_project/", {
            method: "POST",
        })
            .then(() => {
                setLoading(false);
                setOpen(false);
                notify("ScanCode.io project created", {
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
                title="Create ScanCode.io project"
                onClick={handleOpen}
                icon={<AddCircleIcon sx={{ color: getIconAndFontColor() }} />}
            />
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle>Create ScanCode.io project</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={createScanCodeIOProject}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Create"
                                saveButtonIcon={<AddCircleIcon />}
                                alwaysEnable
                            />
                        }
                    >
                        <Fragment />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={loading && open} />
        </Fragment>
    );
};

export default CreateScanCodeIOProject;
