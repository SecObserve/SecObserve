import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { CreateBase, SimpleForm, useCreate, useNotify, useRefresh } from "react-admin";

import AddButton from "../../commons/custom_fields/AddButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required_255 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";

export type ServiceCreateProps = {
    product: any;
};

const ServiceCreate = ({ product }: ServiceCreateProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const [create] = useCreate();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    const create_service = (data: any) => {
        data.product = product.id;

        create(
            "services",
            { data: data },
            {
                onSuccess: () => {
                    refresh();
                    notify("Service added", { type: "success" });
                    setOpen(false);
                },
                onError: (error: any) => {
                    notify(error.message, { type: "warning" });
                },
            }
        );
    };

    return (
        <Fragment>
            <AddButton title="Add service" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Add service</DialogTitle>
                <DialogContent>
                    <CreateBase resource="services">
                        <SimpleForm onSubmit={create_service} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                            <TextInputWide source="name" validate={validate_required_255} autoFocus />
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ServiceCreate;
